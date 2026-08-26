# PowerShell helper to run migrations using Flask-Migrate
# Usage: run from project root or adjust paths
$env:FLASK_APP = "backend/manage.py"
$env:FLASK_ENV = "production"

Write-Output "Installing python requirements (if not already installed)..."
pip install -r backend/requirements.txt

Write-Output "Running migrations (migrations_alembic)..."
cd backend
$previousBootstrapSetting = $env:SKIP_DATABASE_BOOTSTRAP
$env:SKIP_DATABASE_BOOTSTRAP = "1"
try {
    flask db migrate -m "autogen" --directory migrations_alembic
    flask db upgrade --directory migrations_alembic
}
finally {
    if ($null -eq $previousBootstrapSetting) {
        Remove-Item Env:SKIP_DATABASE_BOOTSTRAP -ErrorAction SilentlyContinue
    }
    else {
        $env:SKIP_DATABASE_BOOTSTRAP = $previousBootstrapSetting
    }
}
Write-Output "Migrations complete."
