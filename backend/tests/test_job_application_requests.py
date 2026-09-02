from datetime import date, timedelta

from app.models.job import JobNotification, JobSource
from app.models.service import Category, Service
from app.utils.database import db


def _setup_job_application(client):
    with client.application.app_context():
        category = Category.query.filter_by(name='Government Jobs & Employment').first()
        if not category:
            category = Category(name='Government Jobs & Employment')
            db.session.add(category)
            db.session.flush()
        service = Service.query.filter_by(name='Government Job Application Assistance').first()
        if not service:
            service = Service(
                name='Government Job Application Assistance',
                description='Government recruitment assistance',
                price_inr=999.0,
                category=category,
                is_active=True,
            )
            db.session.add(service)
            db.session.flush()
        else:
            service.price_inr = 999.0
            service.is_active = True
        source = JobSource.query.filter_by(key='employment_news').first()
        if not source:
            source = JobSource(
                key='employment_news',
                name='Employment News',
                listing_url='https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All',
            )
            db.session.add(source)
            db.session.flush()
        job = JobNotification(
            source=source,
            slug='verified-job-application-test',
            external_id='verified-job-application-test',
            content_hash='a' * 64,
            title='Verified Assistant Recruitment',
            organization='Official Recruitment Board',
            application_fee='₹100 for applicable applicants; exemptions may apply',
            official_notice_url='https://employmentnews.gov.in/notice/verified-job',
            application_url='https://employmentnews.gov.in/apply/verified-job',
            deadline=date.today() + timedelta(days=20),
            status='published',
            confidence=0.95,
        )
        db.session.add(job)
        db.session.commit()
        return service.id, job.slug, job.title


def test_job_request_binds_verified_notice_and_uses_30_rupee_assistance_fee(client):
    service_id, job_slug, job_title = _setup_job_application(client)
    registered = client.post('/api/auth/register', json={
        'name':'Job Applicant','phone':'9991112233','email':'job-applicant@example.com','password':'strong-pass1'
    })
    assert registered.status_code == 200
    headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}

    response = client.post('/api/orders/', headers=headers, json={
        'service_id': service_id,
        'application_data': {
            'job_slug': job_slug,
            'job_title': 'Spoofed browser title',
            'job_official_notice_url': 'https://malicious.example/not-real',
            'qualification': 'Degree',
            'exam_region': 'Hyderabad',
        },
    })
    assert response.status_code == 201
    order = response.get_json()['order']
    assert order['fee_inr'] == 30.0
    assert order['official_fee_status'] == 'unconfirmed'
    assert order['official_fee_inr'] is None
    assert order['application_data']['job_title'] == job_title
    assert order['application_data']['job_official_notice_url'].startswith('https://employmentnews.gov.in/')
    assert order['application_data']['job_official_fee'].startswith('₹100')
    assert order['application_data']['qualification'] == 'Degree'


def test_job_request_rejects_unknown_or_closed_notice(client):
    service_id, _job_slug, _job_title = _setup_job_application(client)
    registered = client.post('/api/auth/register', json={
        'name':'Second Applicant','phone':'9991112244','email':'job-applicant-2@example.com','password':'strong-pass2'
    })
    headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}
    response = client.post('/api/orders/', headers=headers, json={
        'service_id': service_id,
        'application_data': {'job_slug': 'not-a-current-verified-job'},
    })
    assert response.status_code == 409
    assert 'unavailable or has closed' in response.get_json()['error']
