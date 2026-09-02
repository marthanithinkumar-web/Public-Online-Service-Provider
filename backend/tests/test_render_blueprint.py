from pathlib import Path


def test_render_start_command_disables_bootstrap_for_entire_startup_chain():
    render_yaml = (Path(__file__).resolve().parents[2] / 'render.yaml').read_text(encoding='utf-8')
    expected = (
        'startCommand: export SKIP_DATABASE_BOOTSTRAP=1; '
        'python pre_migrate.py && flask --app app.main:create_app db upgrade '
        '--directory migrations_alembic && python seed.py && exec gunicorn -c gunicorn.conf.py wsgi:app'
    )
    assert expected in render_yaml
    assert 'SKIP_DATABASE_BOOTSTRAP=1 flask' not in render_yaml
