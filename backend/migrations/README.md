Flask-Migrate / Alembic migration guide

This folder is intended to hold migration scripts created by Flask-Migrate (Alembic).

Generate initial migrations locally (recommended):

1. Ensure requirements are installed:
   python -m pip install -r requirements.txt

2. Initialize migrations (only once):
   python manage.py db init

3. Generate an initial migration based on models:
   python manage.py db migrate -m "initial"

4. Apply the migration to the database:
   python manage.py db upgrade

Notes:
- The project uses Flask-Migrate (Alembic). The migration scripts are not committed here because they must be generated in the developer environment against the installed package versions.
- If you prefer to use Docker, ensure the docker-compose service has the environment variable DATABASE_URL set and run the same manage.py commands inside the container.
- For production, review migration scripts before applying and back up the database.
