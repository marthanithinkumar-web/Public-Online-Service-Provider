Setup Guide

This guide helps you run the project locally for development.

1) Backend (Flask)
- cd backend
- python -m venv venv
- venv\Scripts\activate
- pip install -r requirements.txt
- Copy .env.example to .env and edit SECRET_KEY and DATABASE_URL
- For PostgreSQL local dev, create a database and ensure DATABASE_URL points to it
- Run: python -m app.main

2) Frontend (React + Vite)
- cd frontend
- npm install
- npm run dev

3) Using Docker Compose (recommended):
- Copy backend/.env.example to backend/.env and update values
- docker-compose up --build

Notes
- Admin registration: use /api/auth/register-admin for initial admin creation (requires ADMIN_PASSWORD env value for safety). Remove or restrict this endpoint in production.
- Database migrations: this scaffold uses SQLAlchemy create_all for convenience. For production, add Alembic/Flask-Migrate for schema migrations.
- Never store secrets in source; use environment variables in production.
