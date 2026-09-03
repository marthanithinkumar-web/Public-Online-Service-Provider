from app.models.service import PlatformSetting, Service
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _admin_headers(client):
    with client.application.app_context():
        db.session.add(User(email='recharge-admin@example.com', password_hash=hash_password('strong-pass'), is_admin=True))
        db.session.commit()
    response = client.post('/api/auth/login', json={'email': 'recharge-admin@example.com', 'password': 'strong-pass'})
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def test_recharge_bill_assistance_fee_defaults_to_ten_rupees(client):
    response = client.get('/api/fees/recharge-bill-assistance')
    assert response.status_code == 200
    assert response.get_json()['price_inr'] == 10.0


def test_admin_can_change_recharge_bill_fee_website_wide(client):
    headers = _admin_headers(client)
    with client.application.app_context():
        service = Service(
            name='Recharge & Bill Payments',
            description='Recharge and bill payment assistance',
            price_inr=10,
            official_fee_status='none',
            official_fee_inr=0,
            keywords='mobile recharge,bill payment,dth,fastag,electricity,gas,water,broadband,postpaid',
            is_active=True,
        )
        db.session.add(service)
        db.session.commit()

    response = client.put('/api/fees/recharge-bill-assistance', json={'price_inr': 15}, headers=headers)
    assert response.status_code == 200
    assert response.get_json()['price_inr'] == 15.0

    public_response = client.get('/api/fees/recharge-bill-assistance')
    assert public_response.status_code == 200
    assert public_response.get_json()['price_inr'] == 15.0

    with client.application.app_context():
        assert db.session.get(PlatformSetting, 'recharge_bill_assistance_fee_inr').value == '15.00'
        assert Service.query.filter_by(name='Recharge & Bill Payments').one().price_inr == 15.0
