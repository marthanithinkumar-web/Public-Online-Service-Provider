from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_pre_migrate_historical_cleanup_is_explicit_one_shot_and_fail_closed():
    source = (ROOT / 'backend' / 'pre_migrate.py').read_text(encoding='utf-8')

    assert "os.getenv('RUN_HISTORICAL_ATTACHMENT_PURGE') != '1'" in source
    assert "ATTACHMENT_RETENTION_MARKER = 'historical_attachment_cleanup_20260907'" in source
    assert "marker.value.startswith('completed')" in source
    assert 'purge_historical_client_attachments(apply=True)' in source
    assert "if result['failed_attachments']:" in source
    assert 'raise RuntimeError(' in source
    assert "value = f\"completed:{result['deleted_attachments']}\"" in source
    assert "prepare_additive_job_tables()\n    run_historical_attachment_cleanup()" in source
