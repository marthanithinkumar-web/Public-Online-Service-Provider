from datetime import date, timedelta

from app.jobs.fee_rules import assess_official_fee, normalise_fee_configuration
from app.models.job import JobNotification, JobSource
from app.models.service import Category, Service
from app.utils.database import db


def _job(client):
    with client.application.app_context():
        category = Category.query.filter_by(name='Government Jobs & Employment').first()
        if not category:
            category = Category(name='Government Jobs & Employment')
            db.session.add(category)
            db.session.flush()
        service = Service.query.filter_by(name='Government Job Application Assistance').first()
        if not service:
            service = Service(name='Government Job Application Assistance', description='Job help', price_inr=30, category=category, is_active=True)
            db.session.add(service)
            db.session.flush()
        source = JobSource.query.filter_by(key='fee_test').first()
        if not source:
            source = JobSource(key='fee_test', name='Official Recruitment Board', listing_url='https://example.gov.in/jobs')
            db.session.add(source)
            db.session.flush()
        job = JobNotification(
            source=source,
            slug='person-specific-fee-test',
            external_id='person-specific-fee-test',
            content_hash='f' * 64,
            title='Person Specific Fee Recruitment',
            organization='Official Recruitment Board',
            application_fee='Fee varies by applicant category and exemption rules.',
            official_notice_url='https://example.gov.in/notice',
            deadline=date.today() + timedelta(days=20),
            status='published',
            confidence=1.0,
        )
        factors, rules = normalise_fee_configuration([
            {'key':'gender','label':'Gender','type':'select','options':['Male','Female','Transgender']},
            {'key':'category','label':'Category','type':'select','options':['General','OBC','SC','ST']},
            {'key':'pwd','label':'Person with benchmark disability (PwBD)','type':'boolean'},
        ], [
            {'label':'PwBD exemption','priority':100,'amount_inr':0,'conditions':{'pwd':['Yes']}},
            {'label':'Women exemption','priority':90,'amount_inr':0,'conditions':{'gender':['Female']}},
            {'label':'SC/ST exemption','priority':80,'amount_inr':0,'conditions':{'category':['SC','ST']}},
            {'label':'Standard fee','priority':0,'amount_inr':100,'conditions':{}},
        ])
        job.fee_factors = factors
        job.fee_rules = rules
        from datetime import datetime, timezone
        job.fee_rules_verified_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.add(job)
        db.session.commit()
        return service.id, job.id, job.slug


def test_fee_rules_choose_person_specific_exemption(client):
    _service_id, job_id, _slug = _job(client)
    with client.application.app_context():
        job = db.session.get(JobNotification, job_id)
        exempt = assess_official_fee(job, {'gender':'Male','category':'General','pwd':'Yes'})
        standard = assess_official_fee(job, {'gender':'Male','category':'General','pwd':'No'})
        assert exempt['status'] == 'known'
        assert exempt['amount_inr'] == 0
        assert standard['amount_inr'] == 100


def test_fee_rules_require_every_notification_factor(client):
    _service_id, job_id, _slug = _job(client)
    with client.application.app_context():
        job = db.session.get(JobNotification, job_id)
        result = assess_official_fee(job, {'gender':'Male','category':'General'})
        assert result['status'] == 'missing_factors'
        assert 'Person with benchmark disability (PwBD)' in result['missing']


def test_job_order_snapshots_calculated_official_fee(client):
    service_id, _job_id, slug = _job(client)
    registered = client.post('/api/auth/register', json={'name':'Fee Applicant','phone':'9992223311','email':'fee-applicant@example.com','password':'strong-pass1'})
    headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}
    response = client.post('/api/orders/', headers=headers, json={
        'service_id': service_id,
        'application_data': {'job_slug':slug,'gender':'Male','category':'General','pwd':'No'},
    })
    assert response.status_code == 201
    order = response.get_json()['order']
    assert order['official_fee_status'] == 'known'
    assert order['official_fee_inr'] == 100
    assert order['application_data']['job_official_fee_assessment']['matched_rule'] == 'Standard fee'


def test_job_order_rejects_missing_fee_factor(client):
    service_id, _job_id, slug = _job(client)
    registered = client.post('/api/auth/register', json={'name':'Missing Fee Applicant','phone':'9992223322','email':'missing-fee@example.com','password':'strong-pass2'})
    headers = {'Authorization': f"Bearer {registered.get_json()['token']}"}
    response = client.post('/api/orders/', headers=headers, json={
        'service_id': service_id,
        'application_data': {'job_slug':slug,'gender':'Male','category':'General'},
    })
    assert response.status_code == 400
    assert 'fee-determining details' in response.get_json()['error']
