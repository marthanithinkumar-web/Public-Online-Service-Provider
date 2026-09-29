import os


def _database_url():
    """Use the installed psycopg2 driver for PostgreSQL URLs.

    Neon/other providers may emit an explicit SQLAlchemy +psycopg URL,
    while this project intentionally pins psycopg2-binary. Normalizing the
    driver here keeps production deploys compatible without exposing or
    rewriting the database secret in Render.
    """
    url = os.getenv('DATABASE_URL', 'sqlite:///psp.db')
    if url.startswith('postgresql+psycopg://'):
        return 'postgresql+psycopg2://' + url[len('postgresql+psycopg://'):]
    if url.startswith('postgresql://'):
        return 'postgresql+psycopg2://' + url[len('postgresql://'):]
    if url.startswith('postgres://'):
        return 'postgresql+psycopg2://' + url[len('postgres://'):]
    return url


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
