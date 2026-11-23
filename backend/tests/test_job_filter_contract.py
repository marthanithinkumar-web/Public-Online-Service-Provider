from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from app.jobs.sources import JobItem
from app.jobs.sync import upsert_item
from app.models.job import JobNotification, JobSource
from app.utils.database import db


def _filter_item(external_id, title, job_type='government'):
    return JobItem(
        external_id=external_id,
        title=title,
        organization='Example Recruitment Board',
        official_notice_url='https://www.upsc.gov.in/recruitment/advertisement',
        deadline=date.today() + timedelta(days=20),
        job_type=job_type,
        qualification='Any graduate',
        confidence=0.95,
    )


def test_public_job_filters_match_source_type_featured_and_limit(client):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='upsc').first()
        if source is None:
            source = JobSource(
                key='upsc',
                name='Union Public Service Commission',
                listing_url='https://www.upsc.gov.in/recruitment',
                enabled=True,
            )
            db.session.add(source)
            db.session.commit()
        featured, *_ = upsert_item(source, _filter_item('filter-upsc-featured', 'Graduate Assistant'))
        featured.is_featured = True
        featured.location = 'Hyderabad, Telangana'
        featured.qualification = 'Engineering degree'
        upsert_item(source, _filter_item('filter-upsc-private', 'Graduate Private Assistant', 'private'))
        db.session.commit()
        checked = datetime.now(timezone.utc).replace(tzinfo=None)
        source.last_sync_status = 'success'
        source.last_sync_completed_at = checked
        source.last_successful_sync_at = checked
        source.consecutive_failures = 0
        featured.last_seen_at = checked
        # Persist the source and item freshness evidence before the request runs
        # in a new Flask application context.
        db.session.commit()
        featured_slug = featured.slug

    response = client.get('/api/jobs/?q=UPSC&type=government&featured=true&location=Hyderabad&qualification=Engineering&limit=1')
    assert response.status_code == 200
    assert response.get_json()['total'] == 1
    assert [item['slug'] for item in response.get_json()['items']] == [featured_slug]

    no_match = client.get('/api/jobs/?q=upsc&type=private&featured=true')
    assert no_match.status_code == 200
    assert no_match.get_json()['items'] == []

    wrong_location = client.get('/api/jobs/?q=upsc&type=government&featured=true&location=Delhi')
    assert wrong_location.status_code == 200
    assert wrong_location.get_json()['items'] == []


def test_public_job_deadline_sort_and_pagination_filters(client):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='upsc').first()
        if source is None:
            source = JobSource(
                key='upsc',
                name='Union Public Service Commission',
                listing_url='https://www.upsc.gov.in/recruitment',
                enabled=True,
            )
            db.session.add(source)
            db.session.commit()

        today = datetime.now(ZoneInfo('Asia/Kolkata')).date()
        month_end = date(today.year, today.month, monthrange(today.year, today.month)[1])
        expiring, *_ = upsert_item(source, _filter_item(
            'filter-contract-expiring', 'Filter Contract Expiring',
        ))
        month_end_item, *_ = upsert_item(source, _filter_item(
            'filter-contract-month-end', 'Filter Contract Month End',
        ))
        later, *_ = upsert_item(source, _filter_item(
            'filter-contract-later', 'Filter Contract Later', 'private',
        ))
        expiring.deadline = today + timedelta(days=min(3, max(1, (month_end - today).days)))
        month_end_item.deadline = month_end
        later.deadline = today + timedelta(days=20)
        checked = datetime.now(timezone.utc).replace(tzinfo=None)
        for job in (expiring, month_end_item, later):
            job.location = 'Filter Test City'
            job.qualification = 'Filter Test Degree'
            job.last_seen_at = checked
        source.last_sync_status = 'success'
        source.last_sync_completed_at = checked
        source.last_successful_sync_at = checked
        source.consecutive_failures = 0
        expiring.published_at = checked - timedelta(days=2)
        month_end_item.published_at = checked - timedelta(days=1)
        later.published_at = checked
        db.session.commit()

    base = '/api/jobs/?q=Filter%20Contract&location=Filter%20Test%20City&qualification=Filter%20Test%20Degree'
    closing_soon = client.get(base + '&deadline=closing_soon').get_json()
    expected_closing = {'Filter Contract Expiring'}
    if (month_end - today).days <= 7:
        expected_closing.add('Filter Contract Month End')
    assert {item['title'] for item in closing_soon['items']} == expected_closing
    assert closing_soon['total'] == len(expected_closing)

    this_month = client.get(base + '&deadline=this_month').get_json()
    assert 'Filter Contract Month End' in {item['title'] for item in this_month['items']}

    first_page = client.get(base + '&sort=newest&limit=1&page=1').get_json()
    second_page = client.get(base + '&sort=newest&limit=1&page=2').get_json()
    assert first_page['total'] == second_page['total'] == 3
    assert first_page['page'] == 1 and first_page['limit'] == 1
    assert first_page['items'][0]['title'] == 'Filter Contract Later'
    assert second_page['items'][0]['title'] == 'Filter Contract Month End'

    latest_deadline = client.get(base + '&sort=deadline_latest&limit=3').get_json()
    assert latest_deadline['items'][0]['title'] == 'Filter Contract Later'
