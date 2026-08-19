from sqlalchemy import inspect, text


def ensure_user_schema(db):
    """Repair nullable User columns missing from an older production database.

    This is idempotent and preserves existing user data. It is needed because
    db.create_all() does not alter an already-existing table when the model
    gains new columns.
    """
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    additions = {"name": "VARCHAR(200)", "phone": "VARCHAR(50)"}
    missing = [(name, sql_type) for name, sql_type in additions.items() if name not in columns]
    if not missing:
        return

    with db.engine.begin() as connection:
        for name, sql_type in missing:
            connection.execute(text(f"ALTER TABLE users ADD COLUMN {name} {sql_type}"))
