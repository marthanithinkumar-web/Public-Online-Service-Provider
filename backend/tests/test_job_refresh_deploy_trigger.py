from pathlib import Path


def test_daily_job_refresh_commits_backend_snapshot_marker():
    workflow = Path('.github/workflows/job-notifications.yml').read_text(encoding='utf-8')

    assert 'backend/app/jobs/verified_snapshot.sha256' in workflow
    assert "sha256sum frontend/public/data/jobs.json" in workflow
    assert 'git add frontend/public/data/jobs.json backend/app/jobs/verified_snapshot.sha256' in workflow
    assert 'SNAPSHOT_STATUS_URL' in workflow
    assert "last_sha == expected_sha" in workflow


def test_snapshot_status_exposes_exact_deployed_fingerprint(client):
    response = client.get('/api/jobs/snapshot-status')

    assert response.status_code == 200
    payload = response.get_json()
    expected = Path('backend/app/jobs/verified_snapshot.sha256').read_text(encoding='utf-8').strip()
    assert payload == {'ready': True, 'sha256': expected}
    assert response.headers['Cache-Control'] == 'no-store'
