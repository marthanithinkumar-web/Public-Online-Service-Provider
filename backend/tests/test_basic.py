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

