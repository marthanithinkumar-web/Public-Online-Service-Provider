#!/usr/bin/env python3
"""Refuse a database restore unless the target is clearly non-production."""

from __future__ import annotations

import os
import sys
from urllib.parse import unquote, urlsplit


def database_identity(url: str) -> tuple[str, str]:
    parsed = urlsplit(url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ValueError("database URL must use postgres:// or postgresql://")
    if not parsed.hostname:
        raise ValueError("database URL is missing a hostname")
    database = unquote(parsed.path.lstrip("/"))
    if not database:
        raise ValueError("database URL is missing a database name")

    host = parsed.hostname.lower()
    first, separator, remainder = host.partition(".")
    if first.endswith("-pooler"):
        first = first[: -len("-pooler")]
    normalised_host = first + (separator + remainder if separator else "")
    return normalised_host, database


def validate_target(production_url: str, target_url: str, expected_host: str) -> str:
    production_host, _ = database_identity(production_url)
    target_host, _ = database_identity(target_url)
    expected_normalised = expected_host.strip().lower()
    expected_first, separator, remainder = expected_normalised.partition(".")
    if expected_first.endswith("-pooler"):
        expected_first = expected_first[: -len("-pooler")]
    expected_normalised = expected_first + (separator + remainder if separator else "")

    if target_host == production_host:
        raise ValueError("restore target resolves to the production Neon branch host")
    if target_host != expected_normalised:
        raise ValueError("restore target host does not match EXPECTED_RESTORE_HOST")
    if not target_host.endswith(".neon.tech"):
        raise ValueError("restore target must be a Neon branch endpoint")
    return target_host


def main() -> int:
    try:
        target_host = validate_target(
            os.environ["PRODUCTION_DATABASE_URL"],
            os.environ["RESTORE_TARGET_DATABASE_URL"],
            os.environ["EXPECTED_RESTORE_HOST"],
        )
    except (KeyError, ValueError) as exc:
        print(f"Restore safety check failed: {exc}", file=sys.stderr)
        return 2
    print(target_host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
