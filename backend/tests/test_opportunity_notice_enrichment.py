from datetime import date

from app.jobs import notice_enrichment as jobs
from app.scholarships import source_enrichment as scholarships


def test_job_notice_extracts_client_facing_facts(monkeypatch):
    class Item:
        official_notice_url='https://ssc.gov.in/example.pdf'
        qualification=age_limit=application_fee=vacancies=salary=None
        application_start_date=deadline=None
        summary='Official SSC recruitment notice.'
    text=('Essential Educational Qualification: Degree in Civil Engineering from a recognized University. '
          'Age limit: 18 to 30 years. Application Fee: Rs. 100. Payment mode online. '
          'Total vacancies: 120. Pay Level-6 (Rs. 35400-112400).')
    monkeypatch.setattr(jobs,'_download_pdf',lambda url,session=None:b'pdf')
    monkeypatch.setattr(jobs,'_pdf_text',lambda data:text)
    item=jobs.enrich_job_item(Item())
    assert item.qualification
    assert '18 to 30' in item.age_limit
    assert '100' in item.application_fee
    assert '120' in item.vacancies
    assert item.salary
    assert item.summary.startswith('Verified from the official notification.')


def test_job_notice_extracts_explicit_application_window(monkeypatch):
    class Item:
        official_notice_url='https://ssc.gov.in/chsl.pdf'
        qualification=age_limit=application_fee=vacancies=salary=None
        application_start_date=deadline=None
        summary='Official SSC recruitment notice.'
    text=('Notice of Combined Higher Secondary Examination. Dates for submission of online applications: '
          '07.09.2026 to 30.09.2026. Last date and time for receipt of online applications: 30.09.2026 23:00. '
          'Candidates must read the complete official notice before applying.')
    monkeypatch.setattr(jobs,'_download_pdf',lambda url,session=None:b'pdf')
    monkeypatch.setattr(jobs,'_pdf_text',lambda data:text)
    item=jobs.enrich_job_item(Item())
    assert item.application_start_date==date(2026,9,7)
    assert item.deadline==date(2026,9,30)


def test_job_notice_never_overwrites_existing_verified_fact(monkeypatch):
    class Item:
        official_notice_url='https://ssc.gov.in/example.pdf'
        qualification='Existing qualification'
        age_limit=application_fee=vacancies=salary=None
        application_start_date=date(2099,1,1)
        deadline=date(2099,1,31)
        summary='Existing summary'
    monkeypatch.setattr(jobs,'_download_pdf',lambda url,session=None:b'pdf')
    monkeypatch.setattr(jobs,'_pdf_text',lambda data:'Essential Educational Qualification: Other qualification. Age limit: 18 to 27 years. Dates for submission of online applications: 01.02.2099 to 28.02.2099.')
    item=jobs.enrich_job_item(Item())
    assert item.qualification=='Existing qualification'
    assert item.application_start_date==date(2099,1,1)
    assert item.deadline==date(2099,1,31)
    assert item.summary=='Existing summary'


def test_scholarship_source_context_replaces_generic_eligibility(monkeypatch):
    item={'title':'Example Merit Scholarship','source_type':'official','source_url':'https://scholarships.gov.in/All-Scholarships','eligibility':'Apply only if you meet current eligibility criteria.'}
    monkeypatch.setattr(scholarships,'_source_text',lambda url,session=None:'Example Merit Scholarship\nEligible students must have annual family income below Rs. 4.5 lakh.\nDomicile certificate is required.\nStudent application open till 31-10-2026')
    result=scholarships.enrich_scholarships([item])[0]
    assert '4.5 lakh' in result['eligibility']
    assert 'Domicile certificate' in result['eligibility']
    assert result['eligibility_source']=='official_source_page'
