from datetime import datetime, timezone

from app.models.order import Order
from app.models.payment import Payment
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.jwt_handler import create_token
from app.utils.password import hash_password


def _headers_for(user):
    token = create_token({'user_id': user.id, 'is_admin': bool(user.is_admin), 'token_version': user.token_version})
    return {'Authorization': f'Bearer {token}'}


def _setup_cancelled_paid_order(client):
    with client.application.app_context():
        admin = User(name='Refund Admin', email='refund-admin@example.com', phone='9000000200', password_hash=hash_password('adminpass'), is_admin=True)
        user = User(name='Refund Client', email='refund-client@example.com', phone='9000000201', password_hash=hash_password('clientpass'), is_admin=False)
        category = Category(name='Refund Tests')
        service = Service(name='Refund Test Service', description='Refund test', price_inr=30, official_fee_status='none', official_fee_inr=0, category=category, is_active=True)
        db.session.add_all([admin, user, category, service]); db.session.flush()
        order = Order(order_code='POSP-REFUND-1', client_name=user.name, phone=user.phone, email=user.email, service=service, user_id=user.id, fee_inr=30, official_fee_status='none', official_fee_inr=0, status='Cancelled')
        db.session.add(order); db.session.flush()
        payment = Payment(order_id=order.id, purpose='assistance_fee', amount_paise=3000, currency='INR', status='captured', razorpay_order_id='order_manual_refund_1', razorpay_payment_id='pay_manual_refund_1', captured_at=datetime.now(timezone.utc).replace(tzinfo=None))
        db.session.add(payment); db.session.commit()
        return order.id, _headers_for(admin), _headers_for(user)


def test_admin_records_manual_refund_and_client_sees_proof_metadata(client):
    order_id, admin_headers, client_headers = _setup_cancelled_paid_order(client)
    before = client.get(f'/api/refunds/order/{order_id}', headers=client_headers)
    assert before.status_code == 200
    assert before.get_json()['status'] == 'not_refunded'
    assert before.get_json()['remaining_refundable_inr'] == 30

    first = client.post(f'/api/refunds/order/{order_id}', headers=admin_headers, data={
        'amount_inr': '10',
        'method': 'upi',
        'reference': 'UPI-REF-001',
        'refunded_at': datetime.now(timezone.utc).isoformat(),
        'note': 'Partial refund after client cancellation',
    })
    assert first.status_code == 201
    assert first.get_json()['refund']['reference'] == 'UPI-REF-001'

    summary = client.get(f'/api/refunds/order/{order_id}', headers=client_headers).get_json()
    assert summary['status'] == 'partially_refunded'
    assert summary['refunded_total_inr'] == 10
    assert summary['remaining_refundable_inr'] == 20
    assert summary['refunds'][0]['method'] == 'upi'
    assert summary['refunds'][0]['proof_available'] is False

    second = client.post(f'/api/refunds/order/{order_id}', headers=admin_headers, data={
        'amount_inr': '20',
        'method': 'bank_transfer',
        'reference': 'UTR-REF-002',
        'refunded_at': datetime.now(timezone.utc).isoformat(),
    })
    assert second.status_code == 201
    final = client.get(f'/api/refunds/order/{order_id}', headers=client_headers).get_json()
    assert final['status'] == 'refunded'
    assert final['refunded_total_inr'] == 30
    assert final['remaining_refundable_inr'] == 0


def test_manual_refund_cannot_exceed_remaining_paid_amount(client):
    order_id, admin_headers, _ = _setup_cancelled_paid_order(client)
    response = client.post(f'/api/refunds/order/{order_id}', headers=admin_headers, data={
        'amount_inr': '31',
        'method': 'upi',
        'reference': 'UPI-TOO-MUCH',
        'refunded_at': datetime.now(timezone.utc).isoformat(),
    })
    assert response.status_code == 409
    assert 'remaining refundable amount' in response.get_json()['error']
