from pathlib import Path


def _render_yaml():
    return (Path(__file__).resolve().parents[2] / 'render.yaml').read_text(encoding='utf-8')


def test_render_start_command_disables_bootstrap_for_entire_startup_chain():
    render_yaml = _render_yaml()
    expected = (
        'startCommand: export SKIP_DATABASE_BOOTSTRAP=1; '
        'python pre_migrate.py && flask --app app.main:create_app db upgrade '
        '--directory migrations_alembic && python seed.py && '
        'python -m app.jobs.snapshot_import --path ../frontend/public/data/jobs.json && '
        'exec gunicorn -c gunicorn.conf.py wsgi:app'
    )
    assert expected in render_yaml
    assert 'SKIP_DATABASE_BOOTSTRAP=1 flask' not in render_yaml


def test_render_static_site_uses_single_spa_fallback_for_deep_link_refreshes():
    render_yaml = _render_yaml()
    assert 'source: /*\n        destination: /index.html' in render_yaml
    assert 'source: /services/*' not in render_yaml
    assert 'destination: /services/*/index.html' not in render_yaml
    assert 'source: /jobs\n' not in render_yaml


def test_render_blueprint_stages_pospindia_frontend_with_environment_managed_origin():
    render_yaml = _render_yaml()
    assert 'name: pospindia\n    runtime: static' in render_yaml
    assert 'key: VITE_SITE_URL\n        sync: false' in render_yaml
    assert 'value: https://pospindia.onrender.com' not in render_yaml
    assert 'name: posp\n    runtime: static' not in render_yaml
    assert 'name: public-online-service-provider-ui\n    runtime: static' not in render_yaml


def test_render_blueprint_noindexes_exact_my_orders_route_and_children():
    render_yaml = _render_yaml()
    assert '- path: /my-orders\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
    assert '- path: /my-orders/*\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
