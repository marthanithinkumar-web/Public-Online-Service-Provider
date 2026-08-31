# Database backup and recovery

This runbook protects the production Neon PostgreSQL database with encrypted,
independent daily backups in a private Backblaze B2 bucket. It supplements
Neon's short Free-plan restore history; it does not replace Neon or change the
production database during a backup.

## What is implemented

- GitHub Actions runs at 02:00 Asia/Kolkata each day and can also be started
  manually.
- `pg_dump` uses a client with the same PostgreSQL major version as Neon and
  creates a consistent custom-format archive.
- The archive is encrypted locally with GnuPG AES-256 before upload. The
  unencrypted dump exists only in the temporary GitHub runner directory and is
  removed when the job exits.
- A SHA-256 checksum and a local decrypt plus `pg_restore --list` check must pass.
- The private B2 bucket keeps the newest 14 daily backup sets. Cleanup removes
  exact B2 object versions, not only visible file names, so hidden versions do
  not accumulate against the free storage allowance.
- Restore mode refuses the production Neon branch host, verifies the expected
  temporary branch host, and requires explicit confirmation phrases.

The expected recovery point is at most 24 hours before an incident after the
first successful scheduled run. Recovery remains a deliberate manual operation
so a damaged or incorrect backup cannot automatically overwrite production.

## One-time activation

Do not put any of these credentials in the repository, an issue, a chat message,
or a screenshot.

### 1. Create a dedicated B2 bucket

In Backblaze, create a second bucket used only for database backups:

- Suggested name: `posp-database-backups-2026` (add a unique suffix if needed)
- Files in Bucket: **Private**
- Object Lock: optional; leave disabled for the automated 14-backup retention
  unless a separate immutable-retention policy is designed

Do not reuse `posp-private-documents-2026`. Separate buckets and keys prevent a
compromised website credential from also controlling database backups.

### 2. Create a bucket-restricted B2 application key

Open **Application Keys**, choose **Add a New Application Key**, and use:

- Name: `posp-github-database-backup`
- Bucket: the dedicated database-backup bucket
- Access: **Read and Write**
- File name prefix: `postgres/` when the option is available
- Allow List All Bucket Names: enable it if Backblaze shows the option

Copy the `keyID` and `applicationKey` when they are shown. The application key is
displayed only once. Never use the B2 master key.

### 3. Add GitHub Actions secrets

Open the existing repository, then go to **Settings → Secrets and variables →
Actions → New repository secret**. Add these seven secrets:

| Secret | Value |
| --- | --- |
| `NEON_BACKUP_DATABASE_URL` | Neon's production **unpooled** PostgreSQL URL |
| `BACKUP_ENCRYPTION_PASSPHRASE` | A newly generated random value of at least 32 bytes |
| `B2_BACKUP_BUCKET` | Dedicated backup bucket name |
| `B2_BACKUP_ENDPOINT_URL` | `https://s3.us-east-005.backblazeb2.com` for the current B2 region |
| `B2_BACKUP_KEY_ID` | The bucket-restricted B2 `keyID` |
| `B2_BACKUP_APPLICATION_KEY` | The bucket-restricted B2 `applicationKey` |
| `B2_BACKUP_REGION` | `us-east-005` for the current B2 region |

Generate the encryption value locally and paste it only into the GitHub secret.
For Windows PowerShell:

```powershell
$backupBytes = New-Object byte[] 32
$generator = [Security.Cryptography.RandomNumberGenerator]::Create()
$generator.GetBytes($backupBytes)
$generator.Dispose()
[Convert]::ToBase64String($backupBytes)
```

Store a second copy of that encryption value in a secure password manager. A
backup cannot be decrypted if the value is lost. Rotating it does not re-encrypt
older backups, so keep the old value until all backups made with it expire.

### 4. Run the first backup

Open **GitHub → Actions → Encrypted production database backup → Run workflow**.
A successful run reports the encrypted object name, 14-backup retention, and a
passed archive validation. The B2 bucket should then contain two current files:

- `postgres/posp-postgres-<UTC timestamp>.dump.gpg`
- the matching `.sha256` file

The scheduled backup is not considered active until this first run is green.

## Safe verification and restore

`scripts/restore_postgres_from_b2.sh` defaults to `RESTORE_MODE=verify`. In that
mode it downloads the selected (or newest) archive, checks its checksum,
decrypts it temporarily, and validates the archive without connecting to a
restore database.

A real recovery drill must target a temporary Neon branch endpoint, never the
production branch. Set both `PRODUCTION_DATABASE_URL` and
`RESTORE_TARGET_DATABASE_URL`; the script normalises pooled/unpooled hostnames
and refuses the production host. `EXPECTED_RESTORE_HOST` must exactly match the
temporary branch host. The first confirmation is:

```text
CONFIRM_NON_PRODUCTION_RESTORE=RESTORE_TO_NON_PRODUCTION_ONLY
```

A branch cloned from production is non-empty. Replacing that temporary branch
also requires:

```text
ALLOW_REPLACE_NONEMPTY_TARGET=REPLACE_CONFIRMED_NON_PRODUCTION_TARGET
```

After a successful drill, verify client/admin counts and recent request records
on the temporary branch, record the result, and delete only that temporary
branch. Never change the production connection string during a drill.

## Incident recovery order

1. Stop writes only if an incident is actively corrupting production data.
2. Preserve the current production branch for investigation.
3. Verify the newest backup in `RESTORE_MODE=verify`.
4. Restore into a new temporary Neon branch and validate the application data.
5. Decide on cutover only after validation and a separate explicit approval.
6. Keep the old production branch until the replacement is confirmed healthy.

No script in this repository automatically cuts over or deletes production.
