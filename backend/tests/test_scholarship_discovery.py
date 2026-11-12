from datetime import date, datetime, timezone
import json

import pytest

from app.scholarships.discovery import (
    is_official_url,
    parse_nsp,
    parse_tg_overseas,
    parse_tg_postmatric,
    parse_tg_prematric,
)
from app.scholarships.snapshot import refresh_snapshot


NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)


def source(key, name, url, parser):
    return {'key': key, 'name': name, 'url': url, 'parser': parser}


def test_official_url_allowlist_rejects_lookalikes_and_http():
    assert is_official_url('https://scholarships.gov.in/All-Scholarships')
    assert is_official_url('https://telanganaepass.cgg.gov.in/epassonlinelinks.jsp')
    assert not is_official_url('https://scholarships.gov.in.evil.example/All-Scholarships')
    assert not is_official_url('http://scholarships.gov.in/All-Scholarships')
    assert not is_official_url('https://example.com/?next=scholarships.gov.in')


def test_nsp_parser_discovers_current_scheme_with_deadline_and_metadata():
    html = '''
    <html><body>
      <div>Academic Year 2026-27</div>
      <button>All India Council For Technical Education</button>
      <div>AICTE - Pragati Scholarship Scheme For Girl Students (Technical Degree) (Merit Based Scheme)</div>
      <div>Scheme Open from : 01-06-2026</div>
      <div>Student Application Open till : 31-10-2026</div>
    </body></html>
    '''
    src = source('nsp', 'National Scholarship Portal', 'https://scholarships.gov.in/All-Scholarships', 'nsp')

    items = parse_nsp(html, src, now=NOW)

    assert len(items) == 1
    item = items[0]
    assert item['title'].startswith('AICTE - Pragati Scholarship Scheme For Girl Students')
    assert item['deadline'] == '2026-10-31'
    assert item['academic_year'] == '2026-27'
    assert item['source_type'] == 'official'
    assert item['is_official'] is True
    assert item['application_url'] == 'https://scholarships.gov.in/Students'
    assert item['category'] == 'Merit Based'
    assert item['application_status'] == 'open'
    assert item['status_evidence'] == 'Student Application Open till : 31-10-2026'
    assert item['source_checked_at'] == NOW.isoformat()


def test_telangana_postmatric_and_prematric_parsers_find_fresh_and_renewal():
    post_html = '''
    <div>Academic Year 2026-27</div>
    <a>Postmatric Scholarships For Fresh Registration (2026-27)</a>
    <a>Postmatric Scholarships For Renewal Registration (2026-27)</a>
    <a>Other State Students Pre-Registration 2026-27</a>
    '''
    pre_html = '''
    <div>Academic Year 2026-27</div>
    <a>Prematric Scholarships For SC/ST/PWD Students Fresh Registration 2026-27</a>
    <a>Prematric Scholarships For SC/ST/BC Renewal Registration 2026-27</a>
    '''
    post_source = source('tg_epass_postmatric', 'Telangana ePASS - Post Matric', 'https://telanganaepass.cgg.gov.in/epassonlinelinks.jsp', 'tg_postmatric')
    pre_source = source('tg_epass_prematric', 'Telangana ePASS - Pre Matric', 'https://telanganaepass.cgg.gov.in/PrematricLinks.do', 'tg_prematric')

    post_items = parse_tg_postmatric(post_html, post_source, now=NOW)
    pre_items = parse_tg_prematric(pre_html, pre_source, now=NOW)

    assert len(post_items) == 3
    assert any('Fresh Registration' in item['title'] for item in post_items)
    assert any('Renewal' in item['title'] for item in post_items)
    assert any('Other-State' in item['title'] for item in post_items)
    assert len(pre_items) == 2
    assert any('Fresh Registration' in item['title'] for item in pre_items)
    assert any('Renewal' in item['title'] for item in pre_items)
    assert all(item['region'].startswith('Telangana') for item in post_items + pre_items)


def test_telangana_overseas_parser_excludes_closed_scheme_and_reads_deadline():
    html = '''
    <div>Ambedkar Overseas Vidya Nidhi</div>
    <div>Registration for SC students is open.</div>
    <div>Chief Minister's Overseas Scholarship Scheme for Minorities</div>
    <div>Registrations Closed</div>
    <div>Mahatma Jyothiba Phule Overseas Vidya Nidhi</div>
    <div>Registration for BC and EBC students</div>
    <div>Last Date for Registration: 30-09-2026</div>
    '''
    src = source('tg_epass_overseas', 'Telangana ePASS - Overseas Scholarships', 'https://telanganaepass.cgg.gov.in/OverseasLinks.do', 'tg_overseas')

    items = parse_tg_overseas(html, src, now=NOW)

    assert len(items) == 2
    assert not any('Minority' in item['title'] for item in items)
    ambedkar = next(item for item in items if 'Ambedkar' in item['title'])
    assert ambedkar['deadline'] is None
    assert ambedkar['application_status'] == 'open'
    assert 'Registration for SC students is open' in ambedkar['status_evidence']
    jyothiba = next(item for item in items if 'Jyothiba' in item['title'])
    assert jyothiba['deadline'] == '2026-09-30'
    assert jyothiba['is_official'] is True


def test_snapshot_separates_official_and_private_and_replaces_healthy_source(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text(json.dumps({
        'generated_at': NOW.isoformat(),
        'items': [
            {
                'id': 'old-nsp', 'slug': 'old-nsp', 'title': 'Old NSP Scholarship',
                'provider': 'Government of India', 'source_name': 'National Scholarship Portal',
                'source_url': 'https://scholarships.gov.in/All-Scholarships',
                'application_url': 'https://scholarships.gov.in/Students',
                'deadline': '2026-10-31', 'status': 'active', 'verified_at': NOW.isoformat(),
            },
            {
                'id': 'private', 'slug': 'private', 'title': 'Partner Scholarship',
                'provider': 'Private Foundation', 'source_name': 'Partner Listing',
                'source_url': 'https://partner.example/scholarship',
                'application_url': 'https://partner.example/apply',
                'deadline': '2026-10-31', 'status': 'active', 'verified_at': NOW.isoformat(),
            },
        ],
    }), encoding='utf-8')

    new_item = {
        'id': 'nsp-new', 'slug': 'new-nsp', 'title': 'New NSP Scholarship',
        'provider': 'Government of India', 'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-11-30', 'status': 'active', 'source_key': 'nsp',
        'source_type': 'official', 'is_official': True, 'record_type': 'scholarship',
        'verified_at': NOW.isoformat(), 'last_seen_at': NOW.isoformat(),
        'source_checked_at': NOW.isoformat(), 'application_status': 'open',
        'deadline_type': 'student_application',
        'status_evidence': 'Student Application Open till : 30-11-2026',
    }

    def discoverer(now=None):
        return [new_item], {'nsp': {'ok': True, 'count': 1, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)

    assert payload['official_count'] == 1
    assert payload['private_count'] == 0
    assert payload['stale_source_count'] == 0
    titles = {item['title'] for item in payload['items']}
    assert titles == {'New NSP Scholarship'}
    assert payload['discovery']['source_health']['nsp']['ok'] is True


def test_snapshot_normalizes_neighbouring_nsp_scheme_title_used_as_provider(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text('{"items": []}', encoding='utf-8')
    base = {
        'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-10-31', 'status': 'active', 'source_key': 'nsp',
        'source_type': 'official', 'is_official': True, 'record_type': 'scholarship',
        'verified_at': NOW.isoformat(), 'last_seen_at': NOW.isoformat(),
        'source_checked_at': NOW.isoformat(), 'application_status': 'open',
        'deadline_type': 'student_application',
        'status_evidence': 'Student Application Open till : 31-10-2026',
    }
    bad_aicte = {
        **base,
        'id': 'nsp-aicte-pragati', 'slug': 'aicte-pragati',
        'title': 'AICTE - Pragati Scholarship Scheme For Girl Students',
        'provider': 'AICTE - Swanath Scholarship Scheme (Technical Degree) (Welfare Based Scheme)',
    }
    bad_other = {
        **base,
        'id': 'nsp-pm-usp-jk', 'slug': 'pm-usp-jk',
        'title': 'PM USP Special Scholarship Scheme For Jammu Kashmir And Ladakh',
        'provider': 'AICTE - Swanath Scholarship Scheme (Technical Degree) (Welfare Based Scheme)',
    }

    def discoverer(now=None):
        return [bad_aicte, bad_other], {'nsp': {'ok': True, 'count': 2, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)
    providers = {item['slug']: item['provider'] for item in payload['items']}

    assert providers['aicte-pragati'] == 'All India Council for Technical Education (AICTE)'
    assert providers['pm-usp-jk'] == 'Government of India (via National Scholarship Portal)'
    assert all('Swanath Scholarship Scheme' not in provider for provider in providers.values())


def test_snapshot_preserves_recent_official_entry_when_source_fails(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text(json.dumps({
        'generated_at': NOW.isoformat(),
        'items': [{
            'id': 'nsp-existing', 'slug': 'nsp-existing', 'title': 'Existing NSP Scholarship',
            'provider': 'Government of India', 'source_name': 'National Scholarship Portal',
            'source_url': 'https://scholarships.gov.in/All-Scholarships',
            'application_url': 'https://scholarships.gov.in/Students',
            'deadline': '2026-10-31', 'status': 'active', 'verified_at': NOW.isoformat(),
        }],
    }), encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': False, 'count': 0, 'checked_at': now.isoformat(), 'error': 'timeout'}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)

    assert payload['count'] == 0
    assert payload['items'] == []
    assert payload['stale_source_count'] == 1
    assert payload['stale_items'][0]['stale_source'] is True
    assert payload['stale_items'][0]['title'] == 'Existing NSP Scholarship'


def test_strict_snapshot_refuses_unhealthy_primary_source(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text('{"items": []}', encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': False, 'count': 0, 'checked_at': now.isoformat(), 'error': 'unavailable'}}

    with pytest.raises(RuntimeError, match='National Scholarship Portal discovery failed'):
        refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer, strict=True)

def test_nsp_parser_keeps_closed_beedi_and_open_pm_yasasvi_dates_with_their_own_cards():
    html = '''
    <html><body>
      <div>Academic Year 2026-27</div>
      <div>Ministry of Labour &amp; Employment</div>
      <div>Financial Assistance For Education To The Wards Of Beedi/Cine/IOMC/LSDM- Pre Matric (Welfare Based Scheme)</div>
      <div>Scheme Open from : 01-06-2026</div>
      <div>Student Application Closed on : 31-10-2026</div>
      <div>Defective Application Verification Open till:15-11-2026</div>
      <div>Institute Verification Open till:15-11-2026</div>
      <div>Department of Social Justice &amp; Empowerment (Backward Classes)</div>
      <div>PM YASASVI Central Sector Scheme Of Top Class Education In Schools For OBC, EBC And DNT Students (Merit Based Scheme)</div>
      <div>Scheme Open from : 22-10-2026</div>
      <div>Student Application Open till : 15-11-2026</div>
      <div>Defective Application Verification Open till:30-11-2026</div>
    </body></html>
    '''
    src = source('nsp', 'National Scholarship Portal', 'https://scholarships.gov.in/All-Scholarships', 'nsp')

    items = parse_nsp(html, src, now=NOW)

    beedi = next(item for item in items if 'Beedi' in item['title'])
    yasasvi = next(item for item in items if 'YASASVI' in item['title'])
    assert beedi['deadline'] == '2026-10-31'
    assert beedi['status'] == 'closed'
    assert beedi['application_status'] == 'closed'
    assert beedi['deadline_type'] == 'student_application'
    assert beedi['status_evidence'] == 'Student Application Closed on : 31-10-2026'
    assert yasasvi['deadline'] == '2026-11-15'
    assert yasasvi['status'] == 'active'
    assert yasasvi['application_status'] == 'open'
    assert yasasvi['application_open_date'] == '2026-10-22'
    assert yasasvi['deadline_timezone'] == 'Asia/Kolkata'


def test_nsp_parser_never_uses_verification_deadline_as_application_deadline():
    html = '''
    <div>Academic Year 2026-27</div>
    <div>Financial Assistance For Education To The Wards Of Beedi/Cine/IOMC/LSDM- Pre Matric (Welfare Based Scheme)</div>
    <div>Scheme Open from : 01-06-2026</div>
    <div>Defective Application Verification Open till:15-11-2026</div>
    <div>Institute Verification Open till:15-11-2026</div>
    </body></html>
    '''
    src = source('nsp', 'National Scholarship Portal', 'https://scholarships.gov.in/All-Scholarships', 'nsp')
    assert parse_nsp(html, src, now=NOW) == []

def test_snapshot_excludes_officially_closed_nsp_record_from_active_items_and_keeps_audit_copy(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text('{"items": []}', encoding='utf-8')
    closed = {
        'id': 'nsp-beedi-pre', 'slug': 'beedi-pre', 'title': 'Beedi Pre Matric Scholarship',
        'provider': 'Ministry of Labour & Employment',
        'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-10-31', 'status': 'closed', 'application_status': 'closed',
        'source_key': 'nsp', 'source_type': 'official', 'is_official': True,
        'verified_at': NOW.isoformat(), 'last_seen_at': NOW.isoformat(),
        'status_evidence': 'Student Application Closed on : 31-10-2026',
    }

    def discoverer(now=None):
        return [closed], {'nsp': {'ok': True, 'count': 1, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 11, 7), now=NOW, discovery_func=discoverer)

    assert payload['items'] == []
    assert payload['count'] == 0
    assert payload['closed_count'] == 1
    assert payload['closed_items'][0]['title'] == 'Beedi Pre Matric Scholarship'
    assert payload['closed_items'][0]['closure_reason'] == 'official_status_closed'

def test_nsp_parser_extracts_labeled_dates_when_a_card_renders_all_dates_on_one_line():
    html = '''
    <html><body>
      <div>Academic Year 2026-27</div>
      <div>Financial Assistance For Education To The Wards Of Beedi/Cine/IOMC/LSDM- Pre Matric (Welfare Based Scheme)</div>
      <div>Scheme Open from : 01-06-2026 Student Application Closed on : 31-10-2026 Defective Application Verification Open till:15-11-2026 Institute Verification Open till:15-11-2026</div>
      <div>PM YASASVI Central Sector Scheme Of Top Class Education In Schools For OBC, EBC And DNT Students (Merit Based Scheme)</div>
      <div>Scheme Open from : 22-10-2026 Student Application Open till : 15-11-2026 Defective Application Verification Open till:30-11-2026</div>
    </body></html>
    '''
    src = source('nsp', 'National Scholarship Portal', 'https://scholarships.gov.in/All-Scholarships', 'nsp')

    items = parse_nsp(html, src, now=NOW)

    beedi = next(item for item in items if 'Beedi' in item['title'])
    yasasvi = next(item for item in items if 'YASASVI' in item['title'])
    assert beedi['application_open_date'] == '2026-06-01'
    assert beedi['deadline'] == '2026-10-31'
    assert beedi['status'] == 'closed'
    assert yasasvi['application_open_date'] == '2026-10-22'
    assert yasasvi['deadline'] == '2026-11-15'
    assert yasasvi['status'] == 'active'


def test_snapshot_preserves_closed_items_across_subsequent_refreshes(tmp_path):
    path = tmp_path / 'scholarships.json'
    closed = {
        'id': 'nsp-beedi-pre', 'slug': 'beedi-pre', 'title': 'Beedi Pre Matric Scholarship',
        'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-10-31', 'status': 'closed', 'application_status': 'closed',
        'source_key': 'nsp', 'source_type': 'official', 'is_official': True,
        'status_evidence': 'Student Application Closed on : 31-10-2026',
        'verified_at': NOW.isoformat(), 'last_seen_at': NOW.isoformat(),
    }
    path.write_text(json.dumps({'items': [], 'closed_items': [closed]}), encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': True, 'count': 0, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)

    assert payload['items'] == []
    assert payload['closed_count'] == 1
    assert payload['closed_items'][0]['slug'] == 'beedi-pre'
    assert payload['closed_items'][0]['application_status'] == 'closed'


def test_snapshot_keeps_disappeared_ambiguous_record_for_admin_review(tmp_path):
    path = tmp_path / 'scholarships.json'
    previous = {
        'id': 'nsp-ambiguous', 'slug': 'nsp-ambiguous', 'title': 'Previously Listed Scholarship',
        'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-10-31', 'status': 'active', 'source_key': 'nsp',
        'source_type': 'official', 'is_official': True,
        'verified_at': NOW.isoformat(), 'last_seen_at': NOW.isoformat(),
    }
    path.write_text(json.dumps({'items': [previous]}), encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': True, 'count': 0, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)

    assert payload['items'] == []
    assert payload['unverified_count'] == 1
    assert payload['unverified_items'][0]['slug'] == 'nsp-ambiguous'
    assert payload['unverified_items'][0]['application_status'] == 'unverified'


def test_snapshot_uses_india_date_before_utc_midnight_for_expiry(tmp_path):
    now = datetime(2026, 11, 12, 20, 0, tzinfo=timezone.utc)  # 13 Nov 01:30 IST
    path = tmp_path / 'scholarships.json'
    previous = {
        'id': 'nsp-yesterday', 'slug': 'nsp-yesterday', 'title': 'Yesterday Deadline Scholarship',
        'provider': 'Test Ministry', 'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-11-12', 'status': 'active', 'application_status': 'open',
        'deadline_type': 'student_application', 'status_evidence': 'Student Application Open till : 12-11-2026',
        'source_checked_at': now.isoformat(), 'verified_at': now.isoformat(), 'last_seen_at': now.isoformat(),
        'source_key': 'nsp', 'source_type': 'official', 'is_official': True, 'region': 'India',
    }
    path.write_text(json.dumps({'items': [previous]}), encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': True, 'count': 0, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, now=now, discovery_func=discoverer)

    assert payload['items'] == []
    assert payload['closed_count'] == 1
    assert payload['closed_items'][0]['slug'] == 'nsp-yesterday'
    assert payload['closed_items'][0]['application_status'] == 'closed'


def test_snapshot_keeps_recently_verified_item_missing_from_healthy_source_in_unverified_review(tmp_path):
    now = datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc)
    path = tmp_path / 'scholarships.json'
    previous = {
        'id': 'nsp-disappeared', 'slug': 'nsp-disappeared', 'title': 'Recently Verified Missing Scholarship',
        'provider': 'Test Ministry', 'source_name': 'National Scholarship Portal',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'application_url': 'https://scholarships.gov.in/Students',
        'deadline': '2026-11-30', 'status': 'active', 'application_status': 'open',
        'deadline_type': 'student_application', 'status_evidence': 'Student Application Open till : 30-11-2026',
        'source_checked_at': now.isoformat(), 'verified_at': now.isoformat(), 'last_seen_at': now.isoformat(),
        'source_key': 'nsp', 'source_type': 'official', 'is_official': True, 'region': 'India',
    }
    path.write_text(json.dumps({'items': [previous]}), encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': True, 'count': 0, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 11, 7), now=now, discovery_func=discoverer)

    assert payload['items'] == []
    assert payload['unverified_count'] == 1
    assert payload['unverified_items'][0]['slug'] == 'nsp-disappeared'
    assert payload['unverified_items'][0]['application_status'] == 'unverified'
    assert payload['unverified_items'][0]['review_reason'] == 'not_returned_by_healthy_official_source_parse'
