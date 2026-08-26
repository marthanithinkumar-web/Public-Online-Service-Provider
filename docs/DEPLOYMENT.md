Deployment Guide

This document describes how to build and deploy the Public Online Service Provider project for production.

1) Build frontend (recommended on your machine or CI)
- cd frontend
- npm install
- npm run build
- This will output a production bundle (Vite default: dist/). Ensure the build completes and files are in frontend/dist.

2) Serve frontend with backend or a static host
Option A: Copy frontend build into backend static and serve with Flask
- After successful build, copy the dist/ content into backend/static/ (create the folder if missing)
- The Flask backend already serves static files from backend/static by default (Flask static folder)

Option B: Serve static via Nginx or a CDN
- Upload frontend/dist to a static host (S3 + CloudFront or Netlify) and set FRONTEND_URL to that domain.

3) Configure backend environment
- Copy backend/.env.production.example to backend/.env and set real values (DATABASE_URL, SECRET_KEY, SMTP and S3 credentials)
- Ensure FORCE_HTTPS=1 in production when using HTTPS

4) Database migrations
- Install Python deps: pip install -r backend/requirements.txt
- Initialize migrations (if not yet done): flask db init --directory migrations_alembic
- Generate migration: flask db migrate -m "initial" --directory migrations_alembic
- Apply migration without running model-dependent seed/bootstrap queries first:
  - Linux/macOS: SKIP_DATABASE_BOOTSTRAP=1 flask db upgrade --directory migrations_alembic
  - PowerShell: $env:SKIP_DATABASE_BOOTSTRAP='1'; flask db upgrade --directory migrations_alembic; Remove-Item Env:SKIP_DATABASE_BOOTSTRAP
- Run the normal application startup or seed command after the upgrade succeeds.

5) Run backend with Gunicorn + Nginx (example)
- Install Gunicorn: pip install gunicorn
- Example: gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
- Use Nginx as reverse proxy, serve static files directly from backend/static or a CDN

6) Docker (recommended for reproducible deploy)
- Use docker-compose.prod.yml (optional) which runs a Node build stage for the frontend and copies static into Nginx or the backend image.
- Build: docker-compose -f docker-compose.prod.yml up --build -d

7) Secrets and credentials
- Do NOT store secrets in the repository. Use environment variables or a secret manager.
- Provide SMTP credentials in backend/.env for password reset and verify emails.
- Provide AWS keys and S3_BUCKET in backend/.env for file attachments (optional).

8) Monitoring and backups
- Configure a logging/monitoring solution (CloudWatch, Datadog)
- Schedule database backups

Troubleshooting
- If flask db migrate reports "No changes in schema detected", your models likely match the database â€” proceed to upgrade anyway.
- If npm is not available on your server, build the frontend locally or in CI and deploy the static files.

Contact
- Provider contact is visible in the site header and footer; update frontend/src/services/config.ts to change contact details.
