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
    }

    def discoverer(now=None):
        return [new_item], {'nsp': {'ok': True, 'count': 1, 'checked_at': now.isoformat()}}

    payload = refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer)

    assert payload['official_count'] == 1
    assert payload['private_count'] == 1
    assert payload['stale_source_count'] == 0
    titles = {item['title'] for item in payload['items']}
    assert 'New NSP Scholarship' in titles
    assert 'Old NSP Scholarship' not in titles
    private = next(item for item in payload['items'] if item['title'] == 'Partner Scholarship')
    assert private['source_type'] == 'private'
    assert private['is_official'] is False
    assert payload['discovery']['source_health']['nsp']['ok'] is True


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

    assert payload['count'] == 1
    assert payload['items'][0]['stale_source'] is True
    assert payload['stale_source_count'] == 1


def test_strict_snapshot_refuses_unhealthy_primary_source(tmp_path):
    path = tmp_path / 'scholarships.json'
    path.write_text('{"items": []}', encoding='utf-8')

    def discoverer(now=None):
        return [], {'nsp': {'ok': False, 'count': 0, 'checked_at': now.isoformat(), 'error': 'unavailable'}}

    with pytest.raises(RuntimeError, match='National Scholarship Portal discovery failed'):
        refresh_snapshot(path, today=date(2026, 9, 4), now=NOW, discovery_func=discoverer, strict=True)
