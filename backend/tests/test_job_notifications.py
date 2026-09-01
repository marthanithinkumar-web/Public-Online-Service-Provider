from datetime import date, datetime, timedelta, timezone

from app.jobs.sources import JobItem, SourceDefinition, parse_employment_news, parse_upsc
from app.jobs.snapshot import build_snapshot
from app.jobs.sync import fetch_official_page, sync_is_due, sync_source, trigger_background_sync, upsert_item
from app.models.job import JobNotification, JobSource
from app.models.user import User
from app.utils.database import db
from app.utils.jwt_handler import create_token
from app.utils.password import hash_password


def _admin_headers(client):
    with client.application.app_context():
        admin = User(name='Jobs Admin', email='jobs-admin@example.com', phone='9000000000', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        token = create_token({'user_id': admin.id, 'is_admin': True, 'token_version': admin.token_version})
    return {'Authorization': f'Bearer {token}'}


def _item(**changes):
    values = dict(
        external_id='notice-1', title='Assistant Officer', organization='Official Recruitment Board',
        official_notice_url='https://employmentnews.gov.in/notice/1', deadline=date.today() + timedelta(days=20),
        application_url='https://employmentnews.gov.in/apply/1', qualification='Any graduate', confidence=0.92,
    )
    values.update(changes)
    return JobItem(**values)


def test_employment_news_parser_extracts_only_present_details():
    html = '''<table><tr><th>Advertisement No.</th><th>Organization</th><th>Post</th><th>Mode</th><th>Last Date</th></tr>
    <tr><td>EN-42</td><td>National Test Board</td><td>Assistant Posts</td><td>Online</td><td>30 September 2099</td></tr></table>'''
    items = parse_employment_news(html, 'https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All')
    assert len(items) == 1
    assert items[0].organization == 'National Test Board'
    assert items[0].title == 'Assistant Posts'
    assert items[0].deadline == date(2099, 9, 30)
    assert items[0].qualification is None
    assert items[0].age_limit is None
    assert items[0].application_fee is None


def test_upsc_parser_holds_advertisement_without_deadline_for_review():
    html = '''<ul><li>Advertisement No.52 - 2026 (Special)
    <a href="/sites/default/files/advt-52-2026.pdf">(1.49 MB)</a></li></ul>'''
    items = parse_upsc(html, 'https://www.upsc.gov.in/recruitment/recruitment-advertisement')
    assert len(items) == 1
    assert items[0].organization.startswith('Union Public Service Commission')
    assert items[0].official_notice_url == 'https://www.upsc.gov.in/sites/default/files/advt-52-2026.pdf'
    assert items[0].deadline is None
    assert items[0].confidence < 0.8


def test_sync_publishes_complete_notice_and_queues_uncertain_notice(client, monkeypatch):
    complete = _item()
    uncertain = _item(external_id='notice-2', title='Second Post', deadline=None, confidence=0.65)
    definition = SourceDefinition('employment_news', 'Employment News', 'https://employmentnews.gov.in/jobs', lambda *_: [complete, uncertain])
    monkeypatch.setitem(__import__('app.jobs.sync', fromlist=['SOURCE_BY_KEY']).SOURCE_BY_KEY, 'employment_news', definition)
    monkeypatch.setattr('app.jobs.sync.fetch_official_page', lambda *_args, **_kwargs: '<html/>')
    with client.application.app_context():
        source = JobSource.query.filter_by(key='employment_news').one()
        result = sync_source(source)
        assert result['status'] == 'success'
        assert JobNotification.query.filter_by(external_id='notice-1').one().status == 'published'
        assert JobNotification.query.filter_by(external_id='notice-2').one().status == 'needs_review'


def test_public_job_feed_excludes_review_hidden_and_expired(client):
    with client.application.app_context():
        source = JobSource.query.filter_by(key='employment_news').one()
        visible, *_ = upsert_item(source, _item())
        review, *_ = upsert_item(source, _item(external_id='review', title='Review Post', deadline=None, confidence=0.3))
        expired, *_ = upsert_item(source, _item(external_id='expired', title='Expired Post', deadline=date.today() - timedelta(days=1)))
        hidden, *_ = upsert_item(source, _item(external_id='hidden', title='Hidden Post'))
        hidden.status = 'hidden'
        db.session.commit()
        visible_slug = visible.slug
        assert review.status == 'needs_review'
        assert expired.status == 'expired'
    response = client.get('/api/jobs/')
    assert response.status_code == 200
    assert [item['slug'] for item in response.get_json()['items']] == [visible_slug]
    assert client.get(f'/api/jobs/{visible_slug}').status_code == 200
    assert client.get(f'/api/jobs/{review.slug}').status_code == 404


def test_admin_can_review_and_feature_but_cannot_publish_expired(client):
    headers = _admin_headers(client)
    with client.application.app_context():
        source = JobSource.query.filter_by(key='employment_news').one()
        review, *_ = upsert_item(source, _item(deadline=None, confidence=0.4))
        expired, *_ = upsert_item(source, _item(external_id='past', title='Past Post', deadline=date.today() - timedelta(days=2)))
        db.session.commit()
        review_id, expired_id = review.id, expired.id
    assert client.get('/api/admin/jobs').status_code == 401
    listing = client.get('/api/admin/jobs', headers=headers)
    assert listing.status_code == 200
    updated = client.patch(f'/api/admin/jobs/{review_id}', json={'status': 'published', 'is_featured': True}, headers=headers)
    assert updated.status_code == 200
    assert updated.get_json()['job']['is_featured'] is True
    assert client.patch(f'/api/admin/jobs/{expired_id}', json={'status': 'published'}, headers=headers).status_code == 409


def test_fetch_rejects_redirect_away_from_official_hosts():
    class Response:
        url = 'https://malicious.example/jobs'
        encoding = 'utf-8'
        headers = {'Content-Type': 'text/html'}
        def raise_for_status(self): pass
        def iter_content(self, chunk_size): yield b'<html></html>'
    class Session:
        def get(self, *_args, **_kwargs): return Response()
    try:
        fetch_official_page('https://employmentnews.gov.in/jobs', session=Session())
        assert False, 'redirect must be rejected'
    except ValueError as exc:
        assert 'allowlist' in str(exc)


def test_cross_source_duplicate_is_blocked(client):
    with client.application.app_context():
        first = JobSource.query.filter_by(key='employment_news').one()
        second = JobSource.query.filter_by(key='upsc').one()
        original, *_ = upsert_item(first, _item())
        duplicate, is_new, blocked = upsert_item(second, _item(external_id='different-source-id'))
        db.session.commit()
        assert duplicate.id == original.id
        assert is_new is False
        assert blocked is True
        assert JobNotification.query.count() == 1


def test_refresh_is_due_only_without_a_recent_success(client):
    with client.application.app_context():
        assert sync_is_due() is True
        source = JobSource.query.filter_by(key='employment_news').one()
        source.last_sync_status = 'success'
        source.last_sync_completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
        assert sync_is_due() is False


def test_background_refresh_is_disabled_during_tests(client):
    with client.application.app_context():
        assert trigger_background_sync(client.application) is False


def test_public_snapshot_publishes_only_complete_official_notices():
    pages = {
        'employmentnews.gov.in': '''<table><tr><th>Advertisement No.</th><th>Organization</th><th>Post</th><th>Last Date</th></tr>
        <tr><td>EN-99</td><td>National Test Board</td><td>Assistant Posts</td><td>30 September 2099</td></tr></table>''',
        'upsc.gov.in': '''<ul><li>Advertisement No.52 - 2099, closing date 29 September 2099
        <a href="/sites/default/files/advt-52-2099.pdf">Official recruitment advertisement</a></li></ul>''',
        'ncs.gov.in': '<html><body>No server-embedded job records in this fixture.</body></html>',
    }

    class Response:
        encoding = 'utf-8'
        headers = {'Content-Type': 'text/html; charset=utf-8'}
        def __init__(self, url, body): self.url, self.body = url, body
        def raise_for_status(self): pass
        def iter_content(self, chunk_size): yield self.body.encode()

    class Session:
        def get(self, url, **_kwargs):
            host = next(key for key in pages if key in url)
            return Response(url, pages[host])

    now = datetime(2099, 8, 1, tzinfo=timezone.utc)
    snapshot = build_snapshot(session=Session(), now=now)
    assert snapshot['successful_sources'] == 3
    assert snapshot['count'] == 2
    assert snapshot['review_count'] == 0
    assert all(job['status'] == 'published' for job in snapshot['items'])
    assert all(job['deadline'] for job in snapshot['items'])
    assert all(job['official_notice_url'].startswith('https://') for job in snapshot['items'])


def test_public_snapshot_keeps_verified_open_jobs_during_temporary_source_failure():
    complete = _item(deadline=date(2099, 9, 30))
    html = '''<table><tr><th>Advertisement No.</th><th>Organization</th><th>Post</th><th>Last Date</th></tr>
    <tr><td>notice-1</td><td>Official Recruitment Board</td><td>Assistant Officer</td><td>30 September 2099</td></tr></table>'''

    class Response:
        url = 'https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All'
        encoding = 'utf-8'
        headers = {'Content-Type': 'text/html'}
        def raise_for_status(self): pass
        def iter_content(self, chunk_size): yield html.encode()

    class FirstSession:
        def get(self, url, **_kwargs):
            if 'employmentnews.gov.in' in url: return Response()
            raise RuntimeError('temporary source failure')

    first = build_snapshot(session=FirstSession(), now=datetime(2099, 8, 1, tzinfo=timezone.utc))
    assert first['count'] == 1

    class FailedSession:
        def get(self, *_args, **_kwargs): raise RuntimeError('temporary source failure')

    second = build_snapshot(first, session=FailedSession(), now=datetime(2099, 8, 2, tzinfo=timezone.utc))
    assert second['successful_sources'] == 0
    assert second['count'] == 1
    assert second['items'][0]['title'] == complete.title
