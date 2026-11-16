import os
import subprocess
import sys
from pathlib import Path


def test_render_startup_database_commands_skip_all_database_work_when_flagged(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    database_file = tmp_path / 'must-not-be-created.sqlite'
    env = os.environ.copy()
    env.update({
        'SKIP_DATABASE_BOOTSTRAP': '1',
        'DATABASE_URL': f'sqlite:///{database_file}',
        'RATELIMIT_STORAGE_URI': 'memory://',
        'FLASK_ENV': 'development',
    })
    commands = [
        [sys.executable, 'pre_migrate.py'],
        [sys.executable, '-m', 'flask', '--app', 'app.main:create_app',
         'db', 'upgrade', '--directory', 'migrations_alembic'],
        [sys.executable, 'seed.py'],
        [sys.executable, '-m', 'app.jobs.snapshot_import',
         '--path', str(tmp_path / 'does-not-exist.json')],
    ]

    for command in commands:
        result = subprocess.run(
            command,
            cwd=backend,
            env=env,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        assert result.returncode == 0, (
            f"Startup command failed: {' '.join(command)}\\n"
            f"stdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}"
        )

    assert not database_file.exists(), 'A database connection created the SQLite file despite the skip flag.'
