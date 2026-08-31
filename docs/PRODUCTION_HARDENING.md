Production hardening checklist

This checklist collects the important production steps and minimal code/config changes to make the Public Online Service Provider webapp safe and reliable in production.

1) Secrets & configuration
- Do NOT store secrets in the repository. Use environment variables or a secret manager (Vault, AWS Secrets Manager, Azure KeyVault).
- Ensure backend/.env is stored securely (or injected by orchestration/CI). Replace placeholder values with strong SECRET_KEY, production DATABASE_URL, SMTP and AWS credentials.

2) HTTPS and security headers
- Set FORCE_HTTPS=1 in backend/.env and use a valid TLS certificate (Letâ€™s Encrypt, ACM).
- Review Flask-Talisman CSP and tighten: allow only known script/style sources; avoid unsafe-inline. If you use a CDN for frontend assets, add it to CSP.
- Ensure HSTS (max-age) is set appropriately (e.g. 30d or 1y after initial validation).

3) Rate limiting and storage
- Replace in-memory Flask-Limiter storage with Redis or another persistent store to avoid per-process limits being reset on restart.
- Keep strict rate limits on login, register, password reset, and upload endpoints.

4) File uploads
- Keep allowed file types restricted (pdf, png, jpg, jpeg) and limit file size (MAX_UPLOAD_MB).
- Scan uploaded files for malware before storing or delivering (ClamAV, commercial scanning APIs).
- If using S3: use private bucket + presigned URLs for access; set short TTL and restrict bucket policy.

5) Database & migrations
- Use PostgreSQL in production. Create a dedicated DB user with least privileges.
- Generate migrations locally against a schema-matching DB and review autogen scripts before applying.
- Apply migrations in a maintenance window or with rolling updates.
- Enable DB backups and point-in-time recovery when available.

6) Email
- Use a transactional email provider (SendGrid, SES, Mailgun) with dedicated DNS records (SPF, DKIM).
- Do not send sensitive tokens in email â€” the project currently sends short-lived verify/reset links and pins; ensure TTLs are short.

7) Logging & monitoring
- Configure structured logs (JSON) and send to a log aggregator.
- Monitor error rates, latency, worker crashes, and disk usage for uploads.
- Add healthcheck endpoints and process supervision.

8) Deployment & runtime
- Run the app behind a reverse proxy (Nginx) and use Gunicorn as the WSGI server (example: gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app).
- Make sure static frontend assets are served by Nginx or CDN, not by Flask in high-traffic deployments.
- Use multiple instances behind a load balancer and a shared database and Redis for rate-limiter state and sessions (if used).

9) Backups & recovery
- The repository includes an encrypted daily Neon-to-B2 backup workflow with
  14-backup exact-version retention. Complete the one-time GitHub secret setup
  and first green run in `docs/DATABASE_BACKUP_RECOVERY.md`.
- Test restores only on a separately identified temporary Neon branch. The
  guarded restore script refuses the production branch host and does not
  perform an automatic cutover.
- Keep a retention policy for attachments stored in S3.

10) Optional hardening
- Consider adding Content-Security-Policy nonces for inline scripts if required for analytics/ID tools.
- Add two-factor auth for admin accounts.
- Use secrets rotation and IAM roles for S3 access.

Helpful commands (run where appropriate)
- Install deps: pip install -r backend/requirements.txt
- Run migrations (example):
    cd backend
    flask db migrate -m "autogen" --directory migrations_alembic
    flask db upgrade --directory migrations_alembic
- Build frontend locally or in CI:
    cd frontend
    npm ci
    npm run build
  Copy frontend/dist -> backend/static or deploy dist to CDN.

If you want, I can apply small, targeted code changes to improve CSP or swap the limiter config to use Redis â€” confirm and provide Redis connection if you want me to edit code and add docker-compose entries for Redis.
