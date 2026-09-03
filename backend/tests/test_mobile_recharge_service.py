from app.main import ensure_default_services
from app.models.service import Service


def _ensure_recharge_service(app):
    with app.app_context():
        ensure_default_services()
        service = Service.query.filter_by(name='Mobile Recharge').first()
        assert service is not None
        return service.id, service.slug if hasattr(service, 'slug') else None


def test_mobile_recharge_catalog_is_assistance_only(client, app):
    service_id, _ = _ensure_recharge_service(app)
    response = client.get(f'/api/services/{service_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Mobile Recharge'
    assert float(data['price_inr']) == 10.0
    assert data['official_fee_status'] == 'none'
    assert float(data['official_fee_inr']) == 0.0


def test_mobile_recharge_guided_fields_are_returned(client, app):
    service_id, _ = _ensure_recharge_service(app)
    response = client.get(f'/api/services/{service_id}')
    assert response.status_code == 200
    requirements = response.get_json()['requirements']
    fields = {field['key']: field for field in requirements['fields']}
    assert {'mobile_number', 'operator', 'circle', 'plan_reference', 'recharge_amount'} <= set(fields)
    assert fields['operator']['type'] == 'select'
    assert fields['operator']['options'] == ['Airtel', 'Jio', 'Vi', 'BSNL']
    assert all(fields[key]['required'] for key in ('mobile_number', 'operator', 'circle', 'plan_reference', 'recharge_amount'))
    assert requirements['documents'] == []


def test_mobile_recharge_is_searchable_by_operator(client, app):
    _ensure_recharge_service(app)
    for term in ('mobile recharge', 'airtel', 'jio', 'vi', 'bsnl'):
        response = client.get('/api/services/search', query_string={'q': term})
        assert response.status_code == 200
        assert any(item['name'] == 'Mobile Recharge' for item in response.get_json()), term


def test_recharge_fee_endpoint_has_no_official_fee(client, app):
    _ensure_recharge_service(app)
    response = client.get('/api/fees/recharge-bill-assistance')
    assert response.status_code == 200
    data = response.get_json()
    assert float(data['price_inr']) == 10.0
    assert data['official_fee_status'] == 'none'
    assert float(data['official_fee_inr']) == 0.0
