#!/usr/bin/env bash
set -Eeuo pipefail

umask 077

required_variables=(
  BACKUP_DATABASE_URL
  BACKUP_ENCRYPTION_PASSPHRASE
  B2_BACKUP_BUCKET
  B2_BACKUP_ENDPOINT_URL
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
)

for variable in "${required_variables[@]}"; do
  if [[ -z "${!variable:-}" ]]; then
    echo "Missing required environment variable: ${variable}" >&2
    exit 2
  fi
done

if [[ ! "${B2_BACKUP_ENDPOINT_URL}" =~ ^https://s3\.([a-z0-9-]+)\.backblazeb2\.com/?$ ]]; then
  echo "B2_BACKUP_ENDPOINT_URL must be an HTTPS Backblaze B2 S3 endpoint." >&2
  exit 2
fi
B2_REGION="${BASH_REMATCH[1]}"
export AWS_REGION="${B2_REGION}"
export AWS_DEFAULT_REGION="${B2_REGION}"

if [[ ! "${B2_BACKUP_BUCKET}" =~ ^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$ ]]; then
  echo "B2_BACKUP_BUCKET is not a valid S3-compatible bucket name." >&2
  exit 2
fi
if (( ${#BACKUP_ENCRYPTION_PASSPHRASE} < 24 )); then
  echo "BACKUP_ENCRYPTION_PASSPHRASE must contain at least 24 characters." >&2
  exit 2
fi
if [[ "${AWS_ACCESS_KEY_ID}" =~ [[:space:]] ]] || [[ "${AWS_SECRET_ACCESS_KEY}" =~ [[:space:]] ]]; then
  echo "Backblaze B2 credentials must not contain whitespace." >&2
  exit 2
fi

BACKUP_PREFIX="${BACKUP_PREFIX:-postgres/}"
BACKUP_PREFIX="${BACKUP_PREFIX#/}"
BACKUP_PREFIX="${BACKUP_PREFIX%/}/"
BACKUP_RETENTION_COUNT="${BACKUP_RETENTION_COUNT:-14}"
if [[ "${BACKUP_PREFIX}" == *".."* ]] || [[ ! "${BACKUP_PREFIX}" =~ ^[A-Za-z0-9._/-]+/$ ]]; then
  echo "BACKUP_PREFIX contains unsafe characters." >&2
  exit 2
fi
if [[ ! "${BACKUP_RETENTION_COUNT}" =~ ^[0-9]+$ ]] || (( BACKUP_RETENTION_COUNT < 1 || BACKUP_RETENTION_COUNT > 90 )); then
  echo "BACKUP_RETENTION_COUNT must be between 1 and 90." >&2
  exit 2
fi

for command_name in aws gpg python3 sha256sum base64; do
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
  for command_name in pg_dump pg_restore; do
    command -v "${command_name}" >/dev/null || {
      echo "Required command is not installed: ${command_name}" >&2
      exit 2
    }
  done
fi

public_grants="$(aws s3api get-bucket-acl \
  --bucket "${B2_BACKUP_BUCKET}" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" \
  --region "${B2_REGION}" \
  --query "length(Grants[?Grantee.URI=='http://acs.amazonaws.com/groups/global/AllUsers'])" \
  --output text)"
if [[ "${public_grants}" != "0" ]]; then
  echo "The database-backup bucket is not private; refusing to upload." >&2
  exit 2
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf -- "${WORK_DIR}"' EXIT

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive_name="posp-postgres-${timestamp}.dump.gpg"
object_key="${BACKUP_PREFIX}${archive_name}"
dump_file="${WORK_DIR}/database.dump"
encrypted_file="${WORK_DIR}/${archive_name}"
checksum_file="${encrypted_file}.sha256"
verified_dump="${WORK_DIR}/verified.dump"

echo "Creating a consistent PostgreSQL custom-format backup..."
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  docker run --rm \
    -e BACKUP_DATABASE_URL \
    -v "${WORK_DIR}:/backup" \
    "${POSTGRES_DOCKER_IMAGE}" \
    sh -ceu 'pg_dump --dbname="$BACKUP_DATABASE_URL" --format=custom --compress=9 --no-owner --no-acl --file=/backup/database.dump'
else
  pg_dump --dbname="${BACKUP_DATABASE_URL}" --format=custom --compress=9 --no-owner --no-acl --file="${dump_file}"
fi

if [[ ! -s "${dump_file}" ]]; then
  echo "pg_dump did not create a usable archive." >&2
  exit 1
fi

echo "Encrypting the backup before it leaves the runner..."
printf '%s' "${BACKUP_ENCRYPTION_PASSPHRASE}" | gpg \
  --batch --yes --pinentry-mode loopback --passphrase-fd 0 \
  --symmetric --cipher-algo AES256 --compress-algo none \
  --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65011712 \
  --output "${encrypted_file}" "${dump_file}"
rm -f -- "${dump_file}"

sha256sum "${encrypted_file}" | awk '{print $1}' > "${checksum_file}"

echo "Validating encryption, checksum, and PostgreSQL archive structure..."
expected_checksum="$(tr -d '[:space:]' < "${checksum_file}")"
actual_checksum="$(sha256sum "${encrypted_file}" | awk '{print $1}')"
[[ "${expected_checksum}" == "${actual_checksum}" ]] || {
  echo "Encrypted backup checksum validation failed." >&2
  exit 1
}
printf '%s' "${BACKUP_ENCRYPTION_PASSPHRASE}" | gpg \
  --batch --yes --quiet --pinentry-mode loopback --passphrase-fd 0 \
  --decrypt --output "${verified_dump}" "${encrypted_file}"
if [[ -n "${POSTGRES_DOCKER_IMAGE:-}" ]]; then
  docker run --rm -v "${WORK_DIR}:/backup:ro" "${POSTGRES_DOCKER_IMAGE}" \
    pg_restore --list /backup/verified.dump >/dev/null
else
  pg_restore --list "${verified_dump}" >/dev/null
fi
rm -f -- "${verified_dump}"

echo "Uploading the encrypted archive and checksum to the private B2 bucket..."
aws s3 cp "${encrypted_file}" "s3://${B2_BACKUP_BUCKET}/${object_key}" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" --region "${B2_REGION}" --only-show-errors --no-progress
aws s3 cp "${checksum_file}" "s3://${B2_BACKUP_BUCKET}/${object_key}.sha256" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" --region "${B2_REGION}" --only-show-errors --no-progress

echo "Applying exact-version retention (keeping ${BACKUP_RETENTION_COUNT} daily backups)..."
versions_file="${WORK_DIR}/versions.json"
delete_plan="${WORK_DIR}/delete-plan.tsv"
aws s3api list-object-versions \
  --bucket "${B2_BACKUP_BUCKET}" \
  --prefix "${BACKUP_PREFIX}" \
  --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" \
  --region "${B2_REGION}" \
  --output json > "${versions_file}"
python3 "${SCRIPT_DIR}/b2_backup_catalog.py" \
  --input "${versions_file}" \
  --prefix "${BACKUP_PREFIX}" \
  --keep "${BACKUP_RETENTION_COUNT}" > "${delete_plan}"

deleted_versions=0
while IFS=$'\t' read -r encoded_key encoded_version; do
  [[ -n "${encoded_key}" && -n "${encoded_version}" ]] || continue
  key="$(printf '%s' "${encoded_key}" | base64 --decode)"
  version_id="$(printf '%s' "${encoded_version}" | base64 --decode)"
  aws s3api delete-object \
    --bucket "${B2_BACKUP_BUCKET}" \
    --key "${key}" \
    --version-id "${version_id}" \
    --endpoint-url "${B2_BACKUP_ENDPOINT_URL}" \
    --region "${B2_REGION}" >/dev/null
  deleted_versions=$((deleted_versions + 1))
done < "${delete_plan}"

echo "Backup completed: ${object_key}"
echo "Expired object versions removed: ${deleted_versions}"
if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  echo "object_key=${object_key}" >> "${GITHUB_OUTPUT}"
fi
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  {
    echo "### Encrypted database backup completed"
    echo ""
    echo "- Object: \`${object_key}\`"
    echo "- Retention: ${BACKUP_RETENTION_COUNT} daily backups"
    echo "- Expired object versions removed: ${deleted_versions}"
    echo "- Local decrypt and \`pg_restore --list\` validation: passed"
  } >> "${GITHUB_STEP_SUMMARY}"
fi
