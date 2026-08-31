#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

required_variables=(
  BACKUP_ENCRYPTION_PASSPHRASE
  B2_BACKUP_BUCKET
  B2_BACKUP_ENDPOINT_URL
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_REGION
)
for variable in "${required_variables[@]}"; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Missing required environment variable: ${variable}" >&2
    exit 2
  fi
done

RESTORE_MODE="${RESTORE_MODE:-verify}"
BACKUP_PREFIX="${BACKUP_PREFIX:-postgres/}"
BACKUP_PREFIX="${BACKUP_PREFIX#/}"
BACKUP_PREFIX="${BACKUP_PREFIX%/}/"
if [[ ! "${B2_BACKUP_ENDPOINT_URL}" =~ ^https://s3\.[a-z0-9-]+\.backblazeb2\.com/?$ ]]; then
  echo "B2_BACKUP_ENDPOINT_URL must be an HTTPS Backblaze B2 S3 endpoint." >&2
  exit 2
fi
if [[ ! "${B2_BACKUP_BUCKET}" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]]; then
  echo "B2_BACKUP_BUCKET is not a valid S3-compatible bucket name." >&2
  exit 2
fi
if [[ "${BACKUP_PREFIX}" == *".."* ]] || [[ ! "${BACKUP_PREFIX}" =~ ^[A-Za-z0-9._/-]+/$ ]]; then
  echo "BACKUP_PREFIX contains unsafe characters." >&2
  exit 2
fi
if (( ${#BACKUP_ENCRYPTION_PASSPHRASE} < 24 )); then
  echo "BACKUP_ENCRYPTION_PASSPHRASE must contain at least 24 characters." >&2
  exit 2
fi
if [[ "${RESTORE_MODE}" != "verify" && "${RESTORE_MODE}" != "restore" ]]; then
  echo "RESTORE_MODE must be verify or restore." >&2
  exit 2
fi

for command_name in aws gpg python3 sha256sum; do
  command -v "${command_name}" >/dev/null || {
    echo "Required command is not installed: ${command_name}" >&2
    exit 2
  }
done
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  command -v docker >/dev/null || {
    echo "POSTGRES_DOCKER_IMAGE was set but Docker is not installed." >&2
    exit 2
  }
else
  for command_name in pg_restore psql; do
    command -v "${command_name}" >/dev/null || {
      echo "Required command is not installed: ${command_name}" >&2
      exit 2
    }
  done
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf -- "${WORK_DIR}"' EXIT

object_key="${BACKUP_OBJECT_KEY:-}"
if [[ -z "${object_key}" ]]; then
  object_key="$(aws s3api list-objects-v2 \
    --bucket "${B2_BACKUP_BUCKET}" \
    --prefix "${BACKUP_PREFIX}posp-postgres-" \
    --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" \
    --query 'reverse(sort_by(Contents[?ends_with(Key, `.dump.gpg`)], &LastModified))[0].Key' \
    --output text)"
fi
object_name="${object_key#"${BACKUP_PREFIX}"}"
if [[ "${object_key}" == "None" || "${object_key}" != "${BACKUP_PREFIX}"* || ! "${object_name}" =~ ^posp-postgres-[0-9]{8}T[0-9]{6}Z\.dump\.gpg$ ]]; then
  echo "No valid encrypted backup object was selected." >&2
  exit 1
fi

encrypted_file="${WORK_DIR}/database.dump.gpg"
checksum_file="${WORK_DIR}/database.dump.gpg.sha256"
dump_file="${WORK_DIR}/database.dump"

echo "Downloading ${object_key} and its checksum..."
aws s3 cp "s3://${B2_BACKUP_BUCKET}/${object_key}" "${encrypted_file}" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" --only-show-errors --no-progress
aws s3 cp "s3://${B2_BACKUP_BUCKET}/${object_key}.sha256" "${checksum_file}" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" --only-show-errors --no-progress

expected_checksum="$(tr -d '[:space:]' < "${checksum_file}")"
actual_checksum="$(sha256sum "${encrypted_file}" | awk '{print $1}')"
if [[ ! "${expected_checksum}" =~ ^[a-f0-9]{64}$ || "${expected_checksum}" != "${actual_checksum}" ]]; then
  echo "Backup checksum validation failed." >&2
  exit 1
fi

printf '%s' "${BACKUP_ENCRYPTION_PASSPHRASE}" | gpg \
  --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 0 \
  --decrypt --output "${dump_file}" "${encrypted_file}"
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  docker run --rm -v "${WORK_DIR}:/restore:ro" "${POSTGRES_DOCKER_IMAGE}" \
    pg_restore --list /restore/database.dump >/dev/null
else
  pg_restore --list "${dump_file}" >/dev/null
fi
echo "Backup checksum, decryption, and archive validation passed."

if [[ "${RESTORE_MODE}" == "verify" ]]; then
  echo "Verification-only mode complete; no database was changed."
  exit 0
fi

for variable in PRODUCTION_DATABASE_URL RESTORE_TARGET_DATABASE_URL EXPECTED_RESTORE_HOST CONFIRM_NON_PRODUCTION_RESTORE; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Restore mode requires ${variable}." >&2
    exit 2
  fi
done
if [[ "${CONFIRM_NON_PRODUCTION_RESTORE}" != "RESTORE_TO_NON_PRODUCTION_ONLY" ]]; then
  echo "The non-production restore confirmation phrase is incorrect." >&2
  exit 2
fi

target_host="$(python3 "${SCRIPT_DIR}/check_restore_target.py")"
echo "Restore safety checks passed for non-production host: ${target_host}"

relation_query="SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname !~ '^pg_toast' AND c.relkind IN ('r','p','v','m','S','f');"
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  relation_count="$(docker run --rm -e RESTORE_TARGET_DATABASE_URL "${POSTGRES_DOCKER_IMAGE}" \
    sh -ceu 'psql "$RESTORE_TARGET_DATABASE_URL" -X -v ON_ERROR_STOP=1 -Atqc "$1"' -- "${relation_query}")"
else
  relation_count="$(psql "${RESTORE_TARGET_DATABASE_URL}" -X -v ON_ERROR_STOP=1 -Atqc "${relation_query}")"
fi

restore_options=(--exit-on-error --no-owner --no-acl)
if (( relation_count > 0 )); then
  if [[ "${ALLOW_REPLACE_NONEMPTY_TARGET:-}" != "REPLACE_CONFIRMED_NON_PRODUCTION_TARGET" ]]; then
    echo "Target contains ${relation_count} relations; refusing to replace it without the second confirmation phrase." >&2
    exit 2
  fi
  restore_options+=(--clean --if-exists)
fi

echo "Restoring into the confirmed non-production Neon target..."
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  docker run --rm \
    -e RESTORE_TARGET_DATABASE_URL \
    -v "${WORK_DIR}:/restore:ro" \
    "${POSTGRES_DOCKER_IMAGE}" \
    pg_restore "${restore_options[@]}" --dbname="${RESTORE_TARGET_DATABASE_URL}" /restore/database.dump
else
  pg_restore "${restore_options[@]}" --dbname="${RESTORE_TARGET_DATABASE_URL}" "${dump_file}"
fi

echo "Non-production restore completed successfully for ${target_host}. Production was not modified."
