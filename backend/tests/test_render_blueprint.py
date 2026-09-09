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


def test_render_static_site_serves_seo_snapshots_before_spa_fallback():
    render_yaml = _render_yaml()
    assert 'source: /*\n        destination: /index.html' in render_yaml
    assert 'source: /government-services\n        destination: /government-services/index.html' in render_yaml
    assert 'source: /recharge-bills\n        destination: /recharge-bills/index.html' in render_yaml
    assert 'source: /jobs\n        destination: /jobs/index.html' in render_yaml
    assert 'source: /scholarships\n        destination: /scholarships/index.html' in render_yaml
    # Wildcard rewrites would turn an unknown dynamic slug into a static 404
    # instead of allowing React Router to handle the deep link.
    assert 'source: /services/*' not in render_yaml
    assert 'destination: /services/*/index.html' not in render_yaml
    assert 'source: /jobs/*' not in render_yaml
    assert 'source: /scholarships/*' not in render_yaml
    assert '- path: /services/*\n        name: Content-Type\n        value: text/html; charset=utf-8' in render_yaml
    assert '- path: /jobs/*\n        name: Content-Type\n        value: text/html; charset=utf-8' in render_yaml
    assert '- path: /scholarships/*\n        name: Content-Type\n        value: text/html; charset=utf-8' in render_yaml


def test_render_blueprint_pins_the_only_production_frontend_and_api_origins():
    render_yaml = _render_yaml()
    assert 'name: pospindia\n    runtime: static' in render_yaml
    assert 'key: FRONTEND_URL\n        value: https://pospindia.onrender.com' in render_yaml
    assert 'key: PUBLIC_APP_URL\n        value: https://pospindia.onrender.com' in render_yaml
    assert 'key: CORS_ORIGINS\n        value: https://pospindia.onrender.com' in render_yaml
    assert 'key: VITE_SITE_URL\n        value: https://pospindia.onrender.com' in render_yaml
    assert 'key: VITE_API_URL\n        value: https://public-online-service-provider-api.onrender.com' in render_yaml
    assert 'ADMIN_2FA_ENABLED' not in render_yaml
    assert 'name: posp\n    runtime: static' not in render_yaml
    assert 'name: public-online-service-provider-ui\n    runtime: static' not in render_yaml


def test_repository_has_no_retired_frontend_hostname():
    repository_root = Path(__file__).resolve().parents[2]
    retired_hosts = (
        'public-online-service-provider-' + 'ui.onrender.com',
        'public-online-service-provider-' + 'india.onrender.com',
        'posp-' + 'aphu.onrender.com',
    )
    ignored_parts = {'.git', 'node_modules', '.venv', 'dist', 'build'}
    matches = []
    for path in repository_root.rglob('*'):
        if not path.is_file() or ignored_parts.intersection(path.parts) or path.suffix == '.zip':
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, OSError):
            continue
        for host in retired_hosts:
            if host in content:
                matches.append(f'{path.relative_to(repository_root)}: {host}')
    assert not matches, 'Retired frontend hostnames remain:\n' + '\n'.join(matches)


def test_render_blueprint_noindexes_exact_my_orders_route_and_children():
    render_yaml = _render_yaml()
    assert '- path: /admin\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
    assert '- path: /admin/*\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
    assert '- path: /my-orders\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
    assert '- path: /my-orders/*\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive' in render_yaml
