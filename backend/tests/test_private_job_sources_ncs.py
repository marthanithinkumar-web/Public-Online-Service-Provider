from app.jobs.sources import JobItem


def test_job_item_supports_private_job_type():
    item = JobItem(
        external_id='private-1',
        title='Software Engineer',
        organization='Example Employer',
        official_notice_url='https://example.com/jobs/1',
        job_type='private',
    )
    assert item.job_type == 'private'
