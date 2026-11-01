from datetime import date, timedelta

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
        featured.deadline = date.today() + timedelta(days=5)
        featured.location = 'Hyderabad, Telangana'
        featured.qualification = 'Engineering degree'
        upsert_item(source, _filter_item('filter-upsc-private', 'Graduate Private Assistant', 'private'))
        db.session.commit()
        featured_slug = featured.slug

    response = client.get('/api/jobs/?q=UPSC&type=government&featured=true&limit=1')
    assert response.status_code == 200
    assert response.get_json()['total'] == 1
    assert [item['slug'] for item in response.get_json()['items']] == [featured_slug]

    no_match = client.get('/api/jobs/?q=upsc&type=private&featured=true')
    assert no_match.status_code == 200
    assert no_match.get_json()['items'] == []

    combined = client.get('/api/jobs/?q=UPSC&type=government&featured=true&state=Telangana&education=Engineering')
    assert combined.status_code == 200
    assert combined.get_json()['total'] == 1
    assert combined.get_json()['items'][0]['slug'] == featured_slug

    by_location = client.get('/api/jobs/?location=Hyderabad')
    assert by_location.get_json()['total'] == 1
    by_education = client.get('/api/jobs/?education=Engineering')
    assert by_education.get_json()['total'] == 1
    by_deadline = client.get('/api/jobs/?deadline=closing_soon')
    assert by_deadline.get_json()['total'] == 1

    second_page = client.get('/api/jobs/?q=graduate&limit=1&page=2')
    assert second_page.status_code == 200
    assert second_page.get_json()['total'] == 2
    assert second_page.get_json()['page'] == 2
    assert len(second_page.get_json()['items']) == 1

    reverse_sorted = client.get('/api/jobs/?q=graduate&sort=deadline_desc&limit=1')
    assert reverse_sorted.get_json()['items'][0]['slug'] != featured_slug
