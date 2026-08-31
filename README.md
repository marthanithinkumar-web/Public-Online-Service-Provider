Public Online Service Provider

Overview

Public Online Service Provider is a secure, privacy-first web application that helps busy people request assistance for government and public-service applications. This repository contains a frontend (React + TypeScript) and a backend (Flask + SQLAlchemy) with PostgreSQL as the recommended production database.

Quickstart (development)

Prereqs:
- Git
- Docker & Docker Compose (recommended) OR Python 3.10+ and Node 16+

Using Docker Compose (recommended for dev):
1. Copy .env.example to backend/.env and set values (SECRET_KEY, DATABASE_URL).
2. From repository root run:
   docker-compose up --build
3. Frontend will be available on http://localhost:3000 and backend on http://localhost:5000

Manual (no Docker):
Backend
- cd backend
- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt
- set environment variables from .env.example (or create a .env)
- python -m app.main

Frontend
- cd frontend
- npm install
- npm run dev

Project layout
- frontend: React/TypeScript SPA (search, service detail, request form)
- backend: Flask REST API (services, orders, auth/admin)
- database: SQL schema and seeds
- docs: setup, security and deployment notes

Security & Privacy
- Admin uses email/password authentication (hashed passwords)
- Clients never see other clients' private data via APIs
- Never ask clients for OTPs, banking credentials or other secrets

Next steps
- Add tests, CI, and production deployment docs
- Implement email/SMS notifications
- Add file uploads with secure storage

Production deployment (recommended)

1. Build frontend assets
   - cd frontend
   - npm ci
   - npm run build
   - The build output is frontend/dist

2. Copy build to the backend static folder or serve it via CDN
   - PowerShell helper is available at scripts\build_and_package_frontend.ps1
   - Example: .\scripts\build_and_package_frontend.ps1 -CopyToBackend

3. Configure environment secrets
   - Copy backend/.env.example or backend/.env.production.example to backend/.env
   - Set SECRET_KEY, DATABASE_URL, SMTP settings, S3 settings, and FORCE_HTTPS=1

4. Run database migrations
   - cd backend
   - flask db migrate -m "production init" --directory migrations_alembic
   - flask db upgrade --directory migrations_alembic

5. Launch with Docker Compose
   - docker compose -f docker-compose.prod.yml up --build -d
   - The stack expects the frontend build to already exist in frontend/dist for nginx to serve it

6. Or run directly on a VM / server
   - Install Python, PostgreSQL, Gunicorn, Nginx
   - Run backend as: gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
   - Serve frontend static HTML from frontend/dist via Nginx or a CDN

Recommended production targets
- PostgreSQL database in managed hosting or self-hosted
- Nginx or CDN for static frontend assets
- Gunicorn behind a reverse proxy for Flask API
- Redis for rate-limiter state and future session storage
- SMTP provider like SendGrid / SES / Mailgun for transactional mail

Database backup and recovery
- The repository includes an encrypted daily Neon-to-private-B2 workflow with
  14-backup retention and a production-refusing restore guard.
- Follow `docs/DATABASE_BACKUP_RECOVERY.md` to activate and test it. Never commit
  the Neon URL, B2 application key, or backup encryption passphrase.

License: MIT
