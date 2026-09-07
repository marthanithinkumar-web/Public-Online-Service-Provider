from pathlib import Path


def test_daily_job_refresh_commits_backend_snapshot_marker():
    workflow = Path('.github/workflows/job-notifications.yml').read_text(encoding='utf-8')

    assert 'backend/app/jobs/verified_snapshot.sha256' in workflow
    assert "sha256sum frontend/public/data/jobs.json" in workflow
    assert 'git add frontend/public/data/jobs.json backend/app/jobs/verified_snapshot.sha256' in workflow
