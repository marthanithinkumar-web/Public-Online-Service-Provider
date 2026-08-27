"""Produce a credential-free database fingerprint for migration verification."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime
from urllib.parse import urlparse

from sqlalchemy import MetaData, Table, inspect, select, text

from .database import db


KNOWN_ORDER_CODE = "POSP-2026-4577E9441A"
KNOWN_SUPPORT_MESSAGE = (
    "TEST ONLY — Production launch audit message for "
    "POSP-2026-4577E9441A. No action required."
)


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalise(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest()}
    if isinstance(value, (dict, list, tuple)):
        return json.loads(json.dumps(value, sort_keys=True, default=str))
    return str(value)


def _safe_schema_metadata(inspector, table_name: str) -> dict:
    return {
        "columns": [
            {
                "name": item["name"],
                "type": str(item["type"]),
                "nullable": bool(item.get("nullable", True)),
                "default": str(item.get("default")) if item.get("default") is not None else None,
            }
            for item in inspector.get_columns(table_name, schema="public" if inspector.bind.dialect.name == "postgresql" else None)
        ],
        "primary_key": inspector.get_pk_constraint(table_name),
        "foreign_keys": inspector.get_foreign_keys(table_name),
        "unique_constraints": inspector.get_unique_constraints(table_name),
        "indexes": inspector.get_indexes(table_name),
    }


def _postgres_metadata(connection) -> tuple[list[dict], list[dict]]:
    if connection.dialect.name != "postgresql":
        return [], []
    extensions = [
        {"name": row.name, "version": row.version}
        for row in connection.execute(
            text("SELECT extname AS name, extversion AS version FROM pg_extension ORDER BY extname")
        )
    ]
    sequences = [
        {
            "name": row.name,
            "start": row.start,
            "minimum": row.minimum,
            "maximum": row.maximum,
            "increment": row.increment,
            "cycle": row.cycle,
            "cache": row.cache,
            "last_value": row.last_value,
        }
        for row in connection.execute(
            text(
                """
                SELECT sequencename AS name, start_value AS start,
                       min_value AS minimum, max_value AS maximum,
                       increment_by AS increment, cycle, cache_size AS cache,
                       last_value
                FROM pg_sequences
                WHERE schemaname = 'public'
                ORDER BY sequencename
                """
            )
        )
    ]
    return extensions, sequences


def _provider() -> dict[str, str | None]:
    hostname = urlparse(os.getenv("DATABASE_URL", "")).hostname or ""
    if hostname.endswith(".neon.tech"):
        name = "neon"
    elif hostname.endswith(".render.com"):
        name = "render"
    elif os.getenv("DATABASE_URL", "").startswith("sqlite:"):
        name = "sqlite"
    else:
        name = "other"
    return {
        "name": name,
        "host_sha256": hashlib.sha256(hostname.encode("utf-8")).hexdigest() if hostname else None,
    }


def build_database_manifest() -> dict:
    inspector = inspect(db.engine)
    schema = "public" if db.engine.dialect.name == "postgresql" else None
    table_names = sorted(inspector.get_table_names(schema=schema))
    counts: dict[str, int] = {}
    content_hashes: dict[str, str] = {}
    schema_metadata: dict[str, dict] = {}

    with db.engine.connect() as connection:
        extensions, sequences = _postgres_metadata(connection)
        metadata = MetaData()
        for table_name in table_names:
            table = Table(table_name, metadata, autoload_with=connection, schema=schema)
            row_hashes = []
            row_count = 0
            for row in connection.execute(select(table)):
                row_count += 1
                row_hashes.append(_digest([_normalise(value) for value in row]))
            counts[table_name] = row_count
            content_hashes[table_name] = _digest(sorted(row_hashes))
            schema_metadata[table_name] = _safe_schema_metadata(inspector, table_name)

        known_order_count = 0
        known_message_count = 0
        if "orders" in table_names:
            known_order_count = int(
                connection.execute(
                    text("SELECT count(*) FROM orders WHERE order_code = :code"),
                    {"code": KNOWN_ORDER_CODE},
                ).scalar_one()
            )
        if "support_messages" in table_names:
            known_message_count = int(
                connection.execute(
                    text("SELECT count(*) FROM support_messages WHERE message = :message"),
                    {"message": KNOWN_SUPPORT_MESSAGE},
                ).scalar_one()
            )

    return {
        "provider": _provider(),
        "tables": table_names,
        "counts": counts,
        "content_hashes": content_hashes,
        "schema_sha256": _digest(schema_metadata),
        "extensions": extensions,
        "sequences": sequences,
        "sequences_sha256": _digest(sequences),
        "known_pre_migration_record": {
            "order_count": known_order_count,
            "support_message_count": known_message_count,
        },
    }
