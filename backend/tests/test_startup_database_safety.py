import os
import subprocess
import sys

import pytest
from pathlib import Path


@pytest.mark.parametrize('flags', [
    {'SKIP_DATABASE_BOOTSTRAP': '1'},
    {'RENDER': 'true', 'SKIP_DATABASE_BOOTSTRAP': '0', 'POSP_ALLOW_DATABASE_MIGRATIONS': '1'},
    {'RENDER_SERVICE_ID': 'srv-test', 'SKIP_DATABASE_BOOTSTRAP': '0', 'POSP_ALLOW_DATABASE_MIGRATIONS': '1'},
])
def test_render_startup_database_commands_skip_all_database_work_under_production_guards(tmp_path, flags):
    backend = Path(__file__).resolve().parents[1]
    database_file = tmp_path / 'must-not-be-created.sqlite'
    env = os.environ.copy()
    for key in ('RENDER', 'RENDER_SERVICE_ID', 'POSP_ALLOW_DATABASE_MIGRATIONS', 'SKIP_DATABASE_BOOTSTRAP'):
        env.pop(key, None)
    env.update(flags)
    env.update({
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

    assert not database_file.exists(), 'A database connection created the SQLite file despite the production startup guard.'
