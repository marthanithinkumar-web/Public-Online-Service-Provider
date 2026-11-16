import os


def is_render_environment() -> bool:
    return (
        os.getenv('RENDER', '').strip().lower() in {'1', 'true', 'yes'}
        or bool(os.getenv('RENDER_SERVICE_ID'))
    )


def should_skip_database_startup() -> bool:
    return is_render_environment() or os.getenv('SKIP_DATABASE_BOOTSTRAP') == '1'


def should_skip_alembic_migrations() -> bool:
    if is_render_environment():
        return True
    return (
        os.getenv('SKIP_DATABASE_BOOTSTRAP') == '1'
        and os.getenv('POSP_ALLOW_DATABASE_MIGRATIONS') != '1'
    )
