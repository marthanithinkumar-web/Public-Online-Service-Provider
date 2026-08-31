#!/usr/bin/env python3
"""Build a safe hard-delete plan for versioned B2 database backups."""

from __future__ import annotations

import argparse
import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


BACKUP_NAME = re.compile(
    r"^posp-postgres-(?P<stamp>\d{8}T\d{6}Z)\.dump\.gpg(?P<checksum>\.sha256)?$"
)


@dataclass(frozen=True)
class ObjectVersion:
    key: str
    version_id: str
    stamp: str
    is_checksum: bool


def _normalise_prefix(prefix: str) -> str:
    value = prefix.strip().strip("/")
    return f"{value}/" if value else ""


def _iter_known_versions(payload: dict[str, Any], prefix: str) -> Iterable[ObjectVersion]:
    normalised_prefix = _normalise_prefix(prefix)
    for section in ("Versions", "DeleteMarkers"):
        for item in payload.get(section, []):
            key = str(item.get("Key", ""))
            version_id = str(item.get("VersionId", ""))
            if not key.startswith(normalised_prefix) or not version_id:
                continue
            name = key[len(normalised_prefix) :]
            match = BACKUP_NAME.fullmatch(name)
            if not match:
                continue
            yield ObjectVersion(
                key=key,
                version_id=version_id,
                stamp=match.group("stamp"),
                is_checksum=bool(match.group("checksum")),
            )


def build_delete_plan(
    payload: dict[str, Any], prefix: str = "postgres/", keep: int = 14
) -> list[ObjectVersion]:
    """Return every exact version belonging to backup sets older than ``keep``."""

    if keep < 1:
        raise ValueError("keep must be at least 1")

    versions = list(_iter_known_versions(payload, prefix))
    archive_stamps = sorted(
        {item.stamp for item in versions if not item.is_checksum}, reverse=True
    )
    expired_stamps = set(archive_stamps[keep:])
    return sorted(
        (item for item in versions if item.stamp in expired_stamps),
        key=lambda item: (item.stamp, item.key, item.version_id),
    )


def _encoded(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--prefix", default="postgres/")
    parser.add_argument("--keep", default=14, type=int)
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    for item in build_delete_plan(payload, prefix=args.prefix, keep=args.keep):
        print(f"{_encoded(item.key)}\t{_encoded(item.version_id)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
