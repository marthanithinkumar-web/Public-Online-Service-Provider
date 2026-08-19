from sqlalchemy import inspect, text


def ensure_user_schema(db):
    """Add nullable User columns introduced after the production DB was created.

    This is an idempotent compatibility repair for existing deployments whose
    schema predates the current User model. New databases are unaffected.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}

    additions = {
        "name": "VARCHAR(200)",
        "phone": "VARCHAR(50)",
    }

    missing = [(name, sql_type) for name, sql_type in additions.items() if name not in columns]
    if not missing:
        return

    with db.engine.begin() as connection:
        for name, sql_type in missing:
            connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
