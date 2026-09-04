from app.models.service import Service
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


EXPECTED = {
    'Mobile Postpaid Bill Payment Assistance': {'mobile_number', 'operator', 'circle', 'account_reference', 'bill_amount'},
    'DTH Recharge Assistance': {'dth_operator', 'subscriber_id', 'registered_mobile', 'plan_reference', 'recharge_amount'},
    'Broadband / Landline Bill Payment Assistance': {'provider', 'account_number', 'landline_number', 'circle', 'bill_amount'},
    'FASTag Recharge Assistance': {'fastag_issuer', 'vehicle_registration', 'fastag_reference', 'recharge_amount'},
    'Piped Gas Bill Payment Assistance': {'provider', 'consumer_number', 'location', 'bill_amount'},
}


def _admin_headers(client):
    with client.application.app_context():
        db.session.add(User(email='bill-admin@example.com', password_hash=hash_password('strong-pass'), is_admin=True))
        db.session.commit()
    response = client.post('/api/auth/login', json={'email': 'bill-admin@example.com', 'password': 'strong-pass'})
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def test_missing_bill_payment_services_are_seeded_with_safe_fee_semantics(client):
    catalog = client.get('/api/services').get_json()
    by_catalog_name = {item['catalog_name']: item for item in catalog}

    for name in EXPECTED:
        service = by_catalog_name[name]
        assert service['category'] == 'Recharge & Bill Payments'
        assert float(service['price_inr']) == 10.0
        assert service['official_fee_status'] == 'none'
        assert float(service['official_fee_inr']) == 0.0
        assert service['is_active'] is True


def test_bill_payment_services_expose_guided_non_secret_fields(client):
    catalog = client.get('/api/services').get_json()
    by_catalog_name = {item['catalog_name']: item for item in catalog}

    for name, expected_keys in EXPECTED.items():
        detail = client.get(f"/api/services/{by_catalog_name[name]['id']}")
        assert detail.status_code == 200
        requirements = detail.get_json()['requirements']
        fields = {field['key']: field for field in requirements['fields']}
        assert expected_keys <= set(fields)
        assert not any(field.get('required') for field in fields.values())
        assert requirements['documents'] == []
        safety = requirements['safety_note'].lower()
        assert 'otp' in safety
        assert 'upi pin' in safety
        assert 'cvv' in safety
        assert 'separate from the website assistance fee' in safety
        assert 'authorised provider integration' in safety


def test_bill_payment_services_are_searchable_by_common_terms(client):
    searches = {
        'postpaid bill': 'Mobile Postpaid Bill Payment Assistance',
        'dth recharge': 'DTH Recharge Assistance',
        'broadband bill': 'Broadband / Landline Bill Payment Assistance',
        'fastag': 'FASTag Recharge Assistance',
        'piped gas': 'Piped Gas Bill Payment Assistance',
    }
    for term, catalog_name in searches.items():
        response = client.get('/api/services/search', query_string={'q': term})
        assert response.status_code == 200
        assert any(item['catalog_name'] == catalog_name for item in response.get_json()), term


def test_shared_recharge_bill_fee_update_changes_all_six_services(client):
    headers = _admin_headers(client)
    response = client.put('/api/fees/recharge-bill-assistance', json={'price_inr': 12}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()['price_inr'] == 12

    names = ['Mobile Recharge', *EXPECTED.keys()]
    with client.application.app_context():
        services = Service.query.filter(Service.name.in_(names)).all()
        assert len(services) == 6
        assert all(float(service.price_inr) == 12.0 for service in services)

    public_fee = client.get('/api/fees/recharge-bill-assistance')
    assert public_fee.status_code == 200
    assert public_fee.get_json() == {'price_inr': 12.0, 'official_fee_inr': 0, 'official_fee_status': 'none'}
