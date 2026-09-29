from app.config import _database_url


def test_database_url_normalizes_sqlalchemy_psycopg_driver(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@example.neon.tech/app?sslmode=require")
    assert _database_url() == "postgresql+psycopg2://user:pass@example.neon.tech/app?sslmode=require"


def test_database_url_normalizes_legacy_postgres_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@example.neon.tech/app")
    assert _database_url() == "postgresql+psycopg2://user:pass@example.neon.tech/app"


def test_database_url_preserves_standard_postgresql_scheme(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@example.neon.tech/app")
    assert _database_url() == "postgresql://user:pass@example.neon.tech/app"
