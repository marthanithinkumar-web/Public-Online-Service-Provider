import os
import pytest
from app.main import create_app


def test_app_factory_creates_app():
    app = create_app()
    assert app is not None


def test_index_route():
    app = create_app()
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'Public Online Service Provider API' in data.get('message', '')


def test_migration_mode_skips_model_dependent_bootstrap(monkeypatch, tmp_path):
    import app.main as main_module

    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "migration.db"}')
    monkeypatch.setenv('SKIP_DATABASE_BOOTSTRAP', '1')

    def fail_if_called():
        raise AssertionError('model-dependent bootstrap ran during migration mode')

    monkeypatch.setattr(main_module, 'ensure_default_services', fail_if_called)
    monkeypatch.setattr(main_module, 'ensure_admin_user', fail_if_called)

    app = main_module.create_app()
    assert app is not None


def test_default_upload_limit_matches_client_ten_megabyte_message(monkeypatch):
    monkeypatch.delenv('MAX_UPLOAD_MB', raising=False)
    app = create_app()
    assert app.config['MAX_CONTENT_LENGTH'] == 11 * 1024 * 1024
