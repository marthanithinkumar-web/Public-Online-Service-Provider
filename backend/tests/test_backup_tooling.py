import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _load_script(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_retention_hard_deletes_all_versions_beyond_fourteen(tmp_path):
    catalog = _load_script("b2_backup_catalog.py")
    versions = []
    for day in range(1, 17):
        stamp = f"202608{day:02d}T203000Z"
        base = f"postgres/posp-postgres-{stamp}.dump.gpg"
        versions.extend(
            [
                {"Key": base, "VersionId": f"archive-{day}"},
                {"Key": f"{base}.sha256", "VersionId": f"checksum-{day}"},
            ]
        )
    payload = {"Versions": versions, "DeleteMarkers": []}

    plan = catalog.build_delete_plan(payload, prefix="postgres/", keep=14)

    assert {item.stamp for item in plan} == {
        "20260801T203000Z",
        "20260802T203000Z",
    }
    assert len(plan) == 4


def test_retention_ignores_unrelated_bucket_objects():
    catalog = _load_script("b2_backup_catalog.py")
    payload = {
        "Versions": [
            {"Key": "client-document.pdf", "VersionId": "private-document"},
            {"Key": "postgres/readme.txt", "VersionId": "manual-file"},
        ]
    }
    assert catalog.build_delete_plan(payload, keep=1) == []


def test_restore_target_guard_normalises_pooler_but_refuses_production():
    guard = _load_script("check_restore_target.py")
    production = "postgresql://u:p@ep-production-pooler.us-east-2.aws.neon.tech/app?sslmode=require"
    same_branch = "postgresql://u:p@ep-production.us-east-2.aws.neon.tech/restore?sslmode=require"

    try:
        guard.validate_target(
            production,
            same_branch,
            "ep-production.us-east-2.aws.neon.tech",
        )
    except ValueError as exc:
        assert "production" in str(exc)
    else:
        raise AssertionError("production branch restore was not refused")


def test_restore_target_guard_accepts_expected_temporary_neon_branch():
    guard = _load_script("check_restore_target.py")
    target = guard.validate_target(
        "postgresql://u:p@ep-production.us-east-2.aws.neon.tech/app",
        "postgresql://u:p@ep-restore-test-pooler.us-east-2.aws.neon.tech/app",
        "ep-restore-test.us-east-2.aws.neon.tech",
    )
    assert target == "ep-restore-test.us-east-2.aws.neon.tech"


def test_backup_workflow_and_shell_scripts_have_safety_controls():
    workflow = (ROOT / ".github/workflows/database-backup.yml").read_text()
    backup_script = (ROOT / "scripts/backup_postgres_to_b2.sh").read_text()
    restore_script = (ROOT / "scripts/restore_postgres_from_b2.sh").read_text()

    assert "schedule:" in workflow
    assert "NEON_BACKUP_DATABASE_URL" in workflow
    assert "BACKUP_ENCRYPTION_PASSPHRASE" in workflow
    assert "BACKUP_RETENTION_COUNT: '14'" in workflow
    assert "--cipher-algo AES256" in backup_script
    assert "get-bucket-acl" in backup_script
    assert "backblazeb2\\.com" in backup_script
    assert "list-object-versions" in backup_script
    assert "--version-id" in backup_script
    assert "RESTORE_TO_NON_PRODUCTION_ONLY" in restore_script
    assert "check_restore_target.py" in restore_script


def test_backup_catalog_cli_emits_no_plaintext_keys(tmp_path):
    catalog_path = ROOT / "scripts/b2_backup_catalog.py"
    payload_path = tmp_path / "versions.json"
    payload_path.write_text(
        json.dumps(
            {
                "Versions": [
                    {
                        "Key": f"postgres/posp-postgres-202608{day:02d}T203000Z.dump.gpg",
                        "VersionId": f"version-{day}",
                    }
                    for day in range(1, 4)
                ]
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(catalog_path),
            "--input",
            str(payload_path),
            "--keep",
            "2",
        ],
        check=True,
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    assert "posp-postgres" not in result.stdout
    assert result.stdout.strip()
