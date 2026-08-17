# PowerShell helper to run migrations using Flask-Migrate
# Usage: run from project root or adjust paths
$env:FLASK_APP = "backend/manage.py"
$env:FLASK_ENV = "production"

Write-Output "Installing python requirements (if not already installed)..."
pip install -r backend/requirements.txt

Write-Output "Running migrations (migrations_alembic)..."
cd backend
flask db migrate -m "autogen" --directory migrations_alembic
flask db upgrade --directory migrations_alembic
Write-Output "Migrations complete."
