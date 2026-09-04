import requests

from app.models.payment import Payment
from app.models.service import Category, Service
from app.utils.database import db


def _client_headers(client):
    response = client.post('/api/auth/register', json={
        'name': 'Mode Switch Client',
        'phone': '9993030303',
        'email': 'mode-switch@example.com',
        'password': 'strong-pass1',
    })
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def test_checkout_replaces_stale_provider_order_after_test_to_live_switch(client, monkeypatch):
    headers = _client_headers(client)
    with client.application.app_context():
        category = Category.query.filter_by(name='Razorpay Mode Switch').first()
        if category is None:
            category = Category(name='Razorpay Mode Switch')
            db.session.add(category)
            db.session.flush()
        service = Service(
            name='Razorpay Mode Switch Service',
            description='Mode switch payment test',
            price_inr=30,
            official_fee_inr=0,
            official_fee_status='none',
            category=category,
            is_active=True,
        )
        db.session.add(service)
        db.session.commit()
        service_id = service.id

    created = client.post('/api/orders/', headers=headers, json={
        'service_id': service_id,
        'application_data': {'note': 'mode switch'},
    })
    assert created.status_code == 201
    order_id = created.get_json()['order']['id']

    with client.application.app_context():
        stale = Payment(
            order_id=order_id,
            purpose='assistance_fee',
            amount_paise=3000,
            currency='INR',
            status='created',
            razorpay_order_id='order_test_stale',
        )
        db.session.add(stale)
        db.session.commit()
        stale_id = stale.id

    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_live_example')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'live-secret')

    def stale_get(*args, **kwargs):
        response = requests.Response()
        response.status_code = 404
        raise requests.HTTPError(response=response)

    class CreateResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'id': 'order_live_fresh'}

    monkeypatch.setattr('app.routes.payments.requests.get', stale_get)
    monkeypatch.setattr('app.routes.payments.requests.post', lambda *args, **kwargs: CreateResponse())

    checkout = client.post(
        f'/api/payments/orders/{order_id}/checkout',
        headers=headers,
        json={'purpose': 'assistance_fee'},
    )
    assert checkout.status_code == 201
    payload = checkout.get_json()
    assert payload['key_id'] == 'rzp_live_example'
    assert payload['razorpay_order_id'] == 'order_live_fresh'

    with client.application.app_context():
        stale = db.session.get(Payment, stale_id)
        assert stale.status == 'superseded'
        assert stale.failure_code == 'provider_order_unavailable'
        fresh = Payment.query.filter_by(razorpay_order_id='order_live_fresh').one()
        assert fresh.status == 'created'
        assert fresh.amount_paise == 3000
