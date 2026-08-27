from app.main import ensure_default_services
from app.models.service import Service, PlatformSetting
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _admin_headers(client):
    with client.application.app_context():
        db.session.add(User(email='fee-admin@example.com', password_hash=hash_password('strong-pass'), is_admin=True))
        db.session.commit()
    response = client.post('/api/auth/login', json={'email':'fee-admin@example.com','password':'strong-pass'})
    return {'Authorization':f"Bearer {response.get_json()['token']}"}


def test_admin_configures_distinct_official_and_assistance_fees(client):
    headers = _admin_headers(client)
    response = client.post('/api/services/', json={'name':'Fee Test Service','description':'Assistance','price_inr':50,'official_fee_status':'known','official_fee_inr':120}, headers=headers)
    assert response.status_code == 200
    service = response.get_json()['service']
    assert service['price_inr'] == 50
    assert service['official_fee_status'] == 'known'
    assert service['official_fee_inr'] == 120


def test_known_official_fee_requires_an_amount(client):
    response = client.post('/api/services/', json={'name':'Invalid Fee Service','price_inr':30,'official_fee_status':'known'}, headers=_admin_headers(client))
    assert response.status_code == 400
    assert 'Official fee amount is required' in response.get_json()['error']


def test_unconfirmed_official_fee_does_not_invent_total(client):
    with client.application.app_context():
        service = Service(name='Unconfirmed Fee Service', price_inr=30, official_fee_status='unconfirmed')
        db.session.add(service);db.session.commit()
        data = service.to_dict()
    assert data['official_fee_inr'] is None
    assert data['official_fee_status'] == 'unconfirmed'


def test_admin_can_change_assistance_fee_without_repricing_existing_requests(client):
    admin_headers = _admin_headers(client)
    created_service = client.post(
        '/api/services/',
        json={
            'name': 'Configurable Assistance Service',
            'description': 'A service with an editable private assistance fee.',
            'price_inr': 30,
            'official_fee_status': 'none',
        },
        headers=admin_headers,
    )
    assert created_service.status_code == 200
    service_id = created_service.get_json()['service']['id']

    registration = client.post(
        '/api/auth/register',
        json={
            'name': 'Fee Client',
            'phone': '9990001111',
            'email': 'fee-client@example.com',
            'password': 'strong-pass',
        },
    )
    client_headers = {'Authorization': f"Bearer {registration.get_json()['token']}"}
    first_request = client.post(
        '/api/orders/',
        json={
            'service_id': service_id,
            'contact_method': 'phone',
            'application_data': {'assistance_type': 'First request'},
        },
        headers=client_headers,
    )
    assert first_request.status_code == 201
    first_order = first_request.get_json()['order']
    assert first_order['fee_inr'] == 30

    updated_service = client.put(
        f'/api/services/{service_id}',
        json={'price_inr': 100},
        headers=admin_headers,
    )
    assert updated_service.status_code == 200
    assert updated_service.get_json()['service']['price_inr'] == 100

    saved_first_order = client.get(
        f"/api/orders/{first_order['id']}",
        headers=client_headers,
    )
    assert saved_first_order.status_code == 200
    assert saved_first_order.get_json()['order']['fee_inr'] == 30

    second_request = client.post(
        '/api/orders/',
        json={
            'service_id': service_id,
            'contact_method': 'phone',
            'application_data': {'assistance_type': 'Second request'},
        },
        headers=client_headers,
    )
    assert second_request.status_code == 201
    assert second_request.get_json()['order']['fee_inr'] == 100


def test_global_assistance_fee_update_is_admin_only_and_requires_confirmation(client):
    unauthorized = client.put('/api/admin/services/assistance-fee', json={'price_inr': 50, 'confirm': True})
    assert unauthorized.status_code == 401

    headers = _admin_headers(client)
    unconfirmed = client.put('/api/admin/services/assistance-fee', json={'price_inr': 50}, headers=headers)
    assert unconfirmed.status_code == 400
    assert 'Confirm' in unconfirmed.get_json()['error']
    invalid = client.put('/api/admin/services/assistance-fee', json={'price_inr':'NaN','confirm':True}, headers=headers)
    assert invalid.status_code == 400


def test_admin_changes_fee_across_catalog_without_repricing_existing_requests(client):
    admin_headers = _admin_headers(client)
    created = client.post(
        '/api/services/',
        json={'name':'Bulk Fee Test Service','price_inr':30,'official_fee_status':'none'},
        headers=admin_headers,
    )
    service_id = created.get_json()['service']['id']
    registration = client.post(
        '/api/auth/register',
        json={'name':'Bulk Fee Client','phone':'9990002222','email':'bulk-fee-client@example.com','password':'strong-pass'},
    )
    client_headers = {'Authorization': f"Bearer {registration.get_json()['token']}"}
    submitted = client.post(
        '/api/orders/',
        json={'service_id':service_id,'contact_method':'phone','application_data':{'assistance_type':'Fee snapshot'}},
        headers=client_headers,
    )
    assert submitted.status_code == 201
    order_id = submitted.get_json()['order']['id']

    changed = client.put(
        '/api/admin/services/assistance-fee',
        json={'price_inr':75,'confirm':True},
        headers=admin_headers,
    )
    assert changed.status_code == 200
    result = changed.get_json()
    assert result['price_inr'] == 75
    assert result['affected_services'] >= 1
    assert result['existing_requests_repriced'] is False

    catalog = client.get('/api/services/').get_json()
    assert catalog
    assert all(service['price_inr'] == 75 for service in catalog)
    saved_order = client.get(f'/api/orders/{order_id}', headers=client_headers).get_json()['order']
    assert saved_order['fee_inr'] == 30

    audit = client.get('/api/admin/audit', headers=admin_headers)
    assert audit.status_code == 200
    item = audit.get_json()['items'][0]
    assert item['action'] == 'assistance_fee_bulk_update'
    assert item['details']['new_fee_inr'] == 75


def test_admin_can_set_one_service_and_the_whole_catalog_to_zero(client):
    headers = _admin_headers(client)
    catalog = client.get('/api/services/').get_json()
    service_id = catalog[0]['id']

    single = client.put(
        f'/api/services/{service_id}',
        json={'price_inr': 0},
        headers=headers,
    )
    assert single.status_code == 200
    assert single.get_json()['service']['price_inr'] == 0

    global_update = client.put(
        '/api/admin/services/assistance-fee',
        json={'price_inr': 0, 'confirm': True},
        headers=headers,
    )
    assert global_update.status_code == 200
    assert global_update.get_json()['price_inr'] == 0
    assert all(service['price_inr'] == 0 for service in client.get('/api/services/').get_json())
    with client.application.app_context():
        assert db.session.get(PlatformSetting, 'assistance_fee_inr').value == '0.00'


def test_new_services_inherit_the_persisted_website_wide_fee(client):
    headers = _admin_headers(client)
    changed = client.put(
        '/api/admin/services/assistance-fee',
        json={'price_inr': 65, 'confirm': True},
        headers=headers,
    )
    assert changed.status_code == 200
    created = client.post(
        '/api/services/',
        json={'name': 'New Catalog Service After Fee Change', 'official_fee_status': 'unconfirmed'},
        headers=headers,
    )
    assert created.status_code == 200
    assert created.get_json()['service']['price_inr'] == 65
    with client.application.app_context():
        assert db.session.get(PlatformSetting, 'assistance_fee_inr').value == '65.00'


def test_admin_can_change_and_disable_document_pdf_service(client):
    headers = _admin_headers(client)
    catalog = client.get('/api/services/search?q=document pdf').get_json()
    service = next(item for item in catalog if item['name'] == 'Official Document PDF Access Assistance')

    changed = client.put(f"/api/services/{service['id']}", json={'price_inr': 8}, headers=headers)
    assert changed.status_code == 200
    assert changed.get_json()['service']['price_inr'] == 8
    assert next(item for item in client.get('/api/services/search?q=document pdf').get_json() if item['id'] == service['id'])['price_inr'] == 8

    disabled = client.post(f"/api/services/{service['id']}/active", json={'active': False}, headers=headers)
    assert disabled.status_code == 200
    assert disabled.get_json()['service']['is_active'] is False
    assert all(item['id'] != service['id'] for item in client.get('/api/services/search?q=document pdf').get_json())

    # The normal application-startup catalog bootstrap must preserve an
    # administrator's explicit disabled state.
    with client.application.app_context():
        ensure_default_services()
        assert db.session.get(Service, service['id']).is_active is False
    assert all(item['id'] != service['id'] for item in client.get('/api/services/search?q=document pdf').get_json())
