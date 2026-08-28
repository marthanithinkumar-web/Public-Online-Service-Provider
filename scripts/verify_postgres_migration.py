#!/usr/bin/env python3
"""Compare a source and target PostgreSQL database without printing row data.

Set SOURCE_DATABASE_URL and TARGET_DATABASE_URL to direct (unpooled) connection
strings. The report contains only schema metadata, counts, and one-way hashes;
credentials and record contents are never emitted.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from collections.abc import Iterable

import psycopg2
from psycopg2 import sql


EXPECTED_MARKERS = {
    "order_code": os.getenv("MIGRATION_TEST_ORDER_CODE", "POSP-2026-4577E9441A"),
    "support_message": os.getenv(
        "MIGRATION_TEST_SUPPORT_MESSAGE",
        "TEST ONLY — Production launch audit message for POSP-2026-4577E9441A. No action required.",
    ),
}


def fetch_all(cursor, query: str, params: Iterable[object] = ()) -> list[tuple]:
    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def stable_digest(items: object) -> str:
    encoded = json.dumps(items, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def stable_rows_digest(rows: Iterable[tuple]) -> str:
    """Hash metadata rows independently of the database's collation order."""
    normalized = sorted(
        (list(row) for row in rows),
        key=lambda row: json.dumps(row, separators=(",", ":"), default=str),
    )
    return stable_digest(normalized)


def inspect_database(database_url: str) -> dict[str, object]:
    result: dict[str, object] = {}
    with psycopg2.connect(database_url, connect_timeout=15) as connection:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            tables = [
                row[0]
                for row in fetch_all(
                    cursor,
                    """
                    SELECT tablename
                    FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                    """,
                )
            ]

            counts: dict[str, int] = {}
            content_hashes: dict[str, str] = {}
            for table in tables:
                cursor.execute(
                    sql.SQL("SELECT count(*) FROM {}.{}").format(
                        sql.Identifier("public"), sql.Identifier(table)
                    )
                )
                counts[table] = int(cursor.fetchone()[0])
                cursor.execute(
                    sql.SQL(
                        """
                        SELECT md5(coalesce(string_agg(row_hash, '' ORDER BY row_hash), ''))
                        FROM (
                            SELECT md5(row_to_json(t)::text) AS row_hash
                            FROM {}.{} AS t
                        ) AS rows
                        """
                    ).format(sql.Identifier("public"), sql.Identifier(table))
                )
                content_hashes[table] = cursor.fetchone()[0]

            columns = fetch_all(
                cursor,
                """
                SELECT table_name, ordinal_position, column_name, data_type,
                       udt_name, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """,
            )
            constraints = fetch_all(
                cursor,
                """
                SELECT c.conname, c.contype, c.conrelid::regclass::text,
                       pg_get_constraintdef(c.oid, true)
                FROM pg_catalog.pg_constraint AS c
                JOIN pg_catalog.pg_namespace AS n ON n.oid = c.connamespace
                WHERE n.nspname = 'public'
                ORDER BY c.conrelid::regclass::text, c.conname
                """,
            )
            indexes = fetch_all(
                cursor,
                """
                SELECT tablename, indexname, indexdef
                FROM pg_catalog.pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
                """,
            )
            sequences = fetch_all(
                cursor,
                """
                SELECT sequencename, start_value, min_value, max_value,
                       increment_by, cycle, cache_size, last_value
                FROM pg_catalog.pg_sequences
                WHERE schemaname = 'public'
                ORDER BY sequencename
                """,
            )
            extensions = fetch_all(
                cursor,
                """
                SELECT extname, extversion
                FROM pg_catalog.pg_extension
                ORDER BY extname
                """,
            )
            cursor.execute("SELECT version_num FROM alembic_version")
            alembic_version = cursor.fetchone()[0]
            cursor.execute("SELECT count(*) FROM orders WHERE order_code = %s", (EXPECTED_MARKERS["order_code"],))
            marker_order_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT count(*) FROM support_messages WHERE message = %s", (EXPECTED_MARKERS["support_message"],))
            marker_message_count = int(cursor.fetchone()[0])

    result.update(
        tables=tables,
        counts=counts,
        content_hashes=content_hashes,
        columns_digest=stable_rows_digest(columns),
        constraints_digest=stable_rows_digest(constraints),
        indexes_digest=stable_rows_digest(indexes),
        sequences_digest=stable_rows_digest(sequences),
        extensions=extensions,
        extensions_digest=stable_rows_digest(extensions),
        alembic_version=alembic_version,
        known_pre_migration_record={
            "order_count": marker_order_count,
            "support_message_count": marker_message_count,
        },
    )
    return result


def main() -> int:
    source_url = os.getenv("SOURCE_DATABASE_URL")
    target_url = os.getenv("TARGET_DATABASE_URL")
    if not source_url or not target_url:
        print("SOURCE_DATABASE_URL and TARGET_DATABASE_URL are required.", file=sys.stderr)
        return 2

    source = inspect_database(source_url)
    target = inspect_database(target_url)
    checks = {
        "tables": source["tables"] == target["tables"],
        "counts": source["counts"] == target["counts"],
        "content_hashes": source["content_hashes"] == target["content_hashes"],
        "columns": source["columns_digest"] == target["columns_digest"],
        "constraints": source["constraints_digest"] == target["constraints_digest"],
        "indexes": source["indexes_digest"] == target["indexes_digest"],
        "sequences": source["sequences_digest"] == target["sequences_digest"],
        "extensions": source["extensions_digest"] == target["extensions_digest"],
        "alembic_version": source["alembic_version"] == target["alembic_version"],
        "known_pre_migration_record": (
            source["known_pre_migration_record"] == target["known_pre_migration_record"]
            and target["known_pre_migration_record"] == {
                "order_count": 1,
                "support_message_count": 1,
            }
        ),
    }
    report = {
        "pass": all(checks.values()),
        "checks": checks,
        "source": source,
        "target": target,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
