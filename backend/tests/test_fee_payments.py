import hashlib
import hmac
import json
from datetime import date, timedelta

from app.models.job import JobNotification, JobSource
from app.models.order import Order
from app.models.payment import Payment
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.jwt_handler import create_token
from app.utils.password import hash_password


def _admin_headers(client):
    with client.application.app_context():
        admin = User(name='Fee Admin', email='fee-admin@example.com', phone='9000000100', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        token = create_token({'user_id': admin.id, 'is_admin': True, 'token_version': admin.token_version})
    return {'Authorization': f'Bearer {token}'}


def _client_headers(client, suffix='1'):
    response = client.post('/api/auth/register', json={'name':'Payment Client','phone':f'99900000{suffix}1','email':f'payment-{suffix}@example.com','password':'strong-pass1'})
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def test_admin_can_set_job_assistance_fee_to_zero_and_new_job_request_snapshots_it(client):
    admin_headers = _admin_headers(client)
    response = client.put('/api/fees/job-assistance', headers=admin_headers, json={'price_inr': 0})
    assert response.status_code == 200
    assert response.get_json()['price_inr'] == 0
    assert client.get('/api/fees/job-assistance').get_json()['price_inr'] == 0

    with client.application.app_context():
        category = Category.query.filter_by(name='Government Jobs & Employment').first() or Category(name='Government Jobs & Employment')
        db.session.add(category); db.session.flush()
        service = Service.query.filter_by(name='Government Job Application Assistance').first()
        if not service:
            service = Service(name='Government Job Application Assistance', description='Job assistance', price_inr=0, category=category, is_active=True)
            db.session.add(service); db.session.flush()
        source = JobSource.query.filter_by(key='employment_news').first()
        if not source:
            source = JobSource(key='employment_news', name='Employment News', listing_url='https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All')
            db.session.add(source); db.session.flush()
        job = JobNotification(source=source, slug='zero-fee-job', external_id='zero-fee-job', content_hash='f'*64, title='Zero Fee Test Recruitment', organization='Official Board', official_notice_url='https://employmentnews.gov.in/zero-fee-job', deadline=date.today()+timedelta(days=10), status='published', confidence=.95)
        db.session.add(job); db.session.commit(); service_id=service.id
    headers = _client_headers(client, '2')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'job_slug':'zero-fee-job'}})
    assert created.status_code == 201
    assert created.get_json()['order']['fee_inr'] == 0


def test_combined_checkout_uses_assistance_plus_confirmed_official_fee(client, monkeypatch):
    with client.application.app_context():
        category = Category.query.filter_by(name='Payments').first() or Category(name='Payments')
        db.session.add(category); db.session.flush()
        service = Service(name='Combined Fee Test Service', description='Combined payment', price_inr=30, official_fee_inr=80, official_fee_status='known', category=category, is_active=True)
        db.session.add(service); db.session.commit(); service_id=service.id
    headers = _client_headers(client, '3')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'note':'test'}})
    assert created.status_code == 201
    order_id = created.get_json()['order']['id']

    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_test_key')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'secret')
    captured = {}
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'id':'order_test_123'}
    def fake_post(url, json, auth, timeout):
        captured.update(json)
        return Response()
    monkeypatch.setattr('app.routes.payments.requests.post', fake_post)
    checkout = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose':'request_total'})
    assert checkout.status_code == 201
    assert checkout.get_json()['amount'] == 11000
    assert captured['amount'] == 11000
    assert checkout.get_json()['breakdown']['assistance_fee_inr'] == 30
    assert checkout.get_json()['breakdown']['official_fee_inr'] == 80


def test_combined_checkout_waits_for_admin_but_assistance_can_be_paid(client, monkeypatch):
    with client.application.app_context():
        category = Category.query.filter_by(name='Payments').first() or Category(name='Payments')
        db.session.add(category); db.session.flush()
        service = Service(name='Unconfirmed Fee Test Service', description='Wait for fee', price_inr=30, official_fee_inr=None, official_fee_status='unconfirmed', category=category, is_active=True)
        db.session.add(service); db.session.commit(); service_id=service.id
    headers = _client_headers(client, '4')
    created = client.post('/api/orders/', headers=headers, json={'service_id': service_id, 'application_data': {'note':'test'}})
    order_id = created.get_json()['order']['id']
    monkeypatch.setenv('RAZORPAY_KEY_ID', 'rzp_test_key')
    monkeypatch.setenv('RAZORPAY_KEY_SECRET', 'secret')
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'id':'order_assistance_123'}
    monkeypatch.setattr('app.routes.payments.requests.post', lambda *args, **kwargs: Response())
    checkout = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose':'request_total'})
    assert checkout.status_code == 409
    assert 'not been confirmed' in checkout.get_json()['error']
    assistance = client.post(f'/api/payments/orders/{order_id}/checkout', headers=headers, json={'purpose':'assistance_fee'})
    assert assistance.status_code == 201
    assert assistance.get_json()['amount'] == 3000


def test_capture_webhook_emails_receipt_once_and_client_can_print_it(client, monkeypatch):
    headers = _client_headers(client, '5')
    with client.application.app_context():
        user = User.query.filter_by(email='payment-5@example.com').first()
        category = Category.query.filter_by(name='Receipt Tests').first() or Category(name='Receipt Tests')
        db.session.add(category); db.session.flush()
        service = Service(name='Receipt Test Service', description='Receipt test', price_inr=30, official_fee_inr=80, official_fee_status='known', category=category, is_active=True)
        db.session.add(service); db.session.flush()
        order = Order(order_code='REQ-RECEIPT-1', client_name=user.name, phone=user.phone, email=user.email, service=service, user_id=user.id, fee_inr=30, official_fee_inr=80, official_fee_status='known')
        db.session.add(order); db.session.flush()
        payment = Payment(order_id=order.id, purpose='request_total', amount_paise=11000, currency='INR', status='created', razorpay_order_id='order_receipt_1')
        db.session.add(payment); db.session.commit(); order_id=order.id

    monkeypatch.setenv('RAZORPAY_WEBHOOK_SECRET', 'webhook-secret')
    sent = []
    monkeypatch.setattr('app.routes.payments.send_email', lambda to, subject, body: sent.append((to, subject, body)) or True)
    event = {'event':'payment.captured','payload':{'payment':{'entity':{'id':'pay_receipt_1','order_id':'order_receipt_1'}}}}
    raw = json.dumps(event, separators=(',', ':')).encode()
    signature = hmac.new(b'webhook-secret', raw, hashlib.sha256).hexdigest()
    response = client.post('/api/payments/razorpay/webhook', data=raw, content_type='application/json', headers={'X-Razorpay-Signature': signature})
    assert response.status_code == 200
    assert len(sent) == 1
    assert sent[0][0] == 'payment-5@example.com'
    assert 'REQ-RECEIPT-1' in sent[0][1]
    assert 'Total paid: ₹110.00' in sent[0][2]

    duplicate = client.post('/api/payments/razorpay/webhook', data=raw, content_type='application/json', headers={'X-Razorpay-Signature': signature})
    assert duplicate.status_code == 200
    assert len(sent) == 1

    receipt = client.get(f'/api/payments/orders/{order_id}/receipt', headers=headers)
    assert receipt.status_code == 200
    assert 'Payment Receipt' in receipt.get_data(as_text=True)
    assert '₹110.00' in receipt.get_data(as_text=True)
    status = client.get(f'/api/payments/orders/{order_id}/status', headers=headers).get_json()
    assert status['payment']['receipt_available'] is True
