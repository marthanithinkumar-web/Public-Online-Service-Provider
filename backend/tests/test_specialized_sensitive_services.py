from app.utils.specialized_service_requirements import get_specialized_requirements
from app.scholarships.source_enrichment import enrich_scholarships


def test_aadhaar_bank_seeding_form_collects_only_safe_identifiers():
    req = get_specialized_requirements('Aadhaar - Bank Account Seeding / DBT Assistance')
    keys = {field['key'] for field in req['fields']}
    assert {'bank_name', 'account_last_four', 'aadhaar_last_four', 'dbt_purpose', 'bank_consent_ready'} <= keys
    assert 'account_number' not in keys
    assert 'aadhaar_number' not in keys
    safety = req['safety_note'].lower()
    for secret in ('otp', 'upi pin', 'cvv', 'password'):
        assert secret in safety
    assert req['official_action']['url'].startswith('https://myaadhaar.uidai.gov.in/')


def test_cyber_fraud_form_prioritises_official_emergency_reporting():
    req = get_specialized_requirements('Online Cyber Fraud Complaint Raise Assistance')
    keys = {field['key'] for field in req['fields']}
    assert {'fraud_category', 'incident_datetime', 'amount_lost', 'transaction_reference', 'called_1930', 'ncrp_acknowledgement'} <= keys
    assert req['official_action']['phone'] == '1930'
    assert 'cybercrime.gov.in' in req['official_action']['url']
    assert 'do not wait' in req['safety_note'].lower()


class FakeResponse:
    url = 'https://scholarships.gov.in/All-Scholarships'
    text = '''
    <h3>Example Student Scholarship</h3>
    <p>Eligibility: students with annual family income not exceeding Rs. 250000.</p>
    <p>Scholarship amount Rs. 12000 per year.</p>
    <p>Documents: income certificate and marksheet.</p>
    <p>Student Application Open till : 31-10-2026</p>
    '''
    def raise_for_status(self):
        return None


class FakeSession:
    def get(self, *args, **kwargs):
        return FakeResponse()


def test_scholarship_enrichment_keeps_scheme_facts_structured_and_adds_nsp_otr_note():
    items = [{
        'title': 'Example Student Scholarship',
        'source_type': 'official',
        'source_key': 'nsp',
        'source_url': 'https://scholarships.gov.in/All-Scholarships',
        'eligibility': 'Apply only if you meet the current eligibility criteria published by the official provider.',
    }]
    enriched = enrich_scholarships(items, session=FakeSession())[0]
    assert enriched['eligibility_source'] == 'official_source_page'
    assert enriched['income_limit'] == '₹250000'
    assert enriched['award'].lower().startswith('rs. 12000')
    assert enriched['documents']
    assert 'One Time Registration (OTR) is mandatory' in enriched['application_requirements_note']
