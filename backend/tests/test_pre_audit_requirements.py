from datetime import datetime
from types import SimpleNamespace

from app.jobs.fee_rules import assess_official_fee
from app.scholarships import source_enrichment


def test_missing_job_fee_factors_are_non_blocking():
    job = SimpleNamespace(
        fee_factors=[{'key': 'category', 'label': 'Category'}],
        fee_rules=[{'amount_inr': 100, 'conditions': {'category': ['General']}, 'label': 'General fee'}],
        fee_rules_verified_at=datetime.utcnow(),
    )

    result = assess_official_fee(job, {})

    assert result['status'] == 'unconfirmed'
    assert result['amount_inr'] is None
    assert result['missing'] == ['Category']


def test_scholarship_enrichment_does_not_mix_adjacent_schemes(monkeypatch):
    source_text = '''
    National Means Cum Merit Scholarship
    Student Application Open till : 30-09-2026
    PM-USP Central Sector Scheme Of Scholarship For College And University Students CSSS
    Family income must be below Rs. 4,50,000 per annum
    Minimum 80 percentage marks required
    '''
    monkeypatch.setattr(source_enrichment, '_source_text', lambda url, session=None: source_text)
    items = [
        {
            'title': 'National Means Cum Merit Scholarship',
            'source_url': 'https://scholarships.gov.in/All-Scholarships',
            'source_type': 'official',
            'source_key': 'nsp',
            'eligibility': '',
        },
        {
            'title': 'PM-USP Central Sector Scheme Of Scholarship For College And University Students CSSS',
            'source_url': 'https://scholarships.gov.in/All-Scholarships',
            'source_type': 'official',
            'source_key': 'nsp',
            'eligibility': '',
        },
    ]

    enriched = source_enrichment.enrich_scholarships(items)

    assert '4,50,000' not in enriched[0]['eligibility']
    assert enriched[0]['eligibility_source'] == 'official_source_unstructured'
    assert '4,50,000' in enriched[1]['eligibility']
    assert enriched[1]['eligibility_source'] == 'official_source_page'
