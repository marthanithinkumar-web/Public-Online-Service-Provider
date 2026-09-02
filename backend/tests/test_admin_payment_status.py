from app.models.order import Order
from app.models.payment import Payment
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.jwt_handler import create_token
from app.utils.password import hash_password


def _admin_headers(client):
    with client.application.app_context():
        admin = User(name='Payment Admin', email='payment-admin@example.com', phone='9000000991', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        token = create_token({'user_id': admin.id, 'is_admin': True, 'token_version': admin.token_version})
    return {'Authorization': f'Bearer {token}'}


def test_admin_can_see_component_payment_status_for_application(client):
    headers = _admin_headers(client)
    with client.application.app_context():
        category = Category.query.filter_by(name='Payments').first() or Category(name='Payments')
        db.session.add(category)
        db.session.flush()
        service = Service(name='Admin Payment Status Test', description='test', price_inr=30, official_fee_inr=80, official_fee_status='known', category=category, is_active=True)
        user = User(name='Client', email='admin-payment-client@example.com', phone='9000000992', password_hash=hash_password('clientpass'))
        db.session.add_all([service, user])
        db.session.flush()
        order = Order(order_code='REQ-ADMIN-PAY-1', client_name=user.name, phone=user.phone, email=user.email, service=service, user_id=user.id, fee_inr=30, official_fee_inr=80, official_fee_status='known')
        db.session.add(order)
        db.session.flush()
        db.session.add(Payment(order_id=order.id, purpose='assistance_fee', amount_paise=3000, currency='INR', status='captured', razorpay_order_id='order_admin_pay_1', razorpay_payment_id='pay_admin_pay_1'))
        db.session.commit()
        order_id = order.id

    response = client.get(f'/api/admin/orders/{order_id}/payments', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['paid_components']['assistance_fee'] is True
    assert data['paid_components']['official_fee'] is False
    assert data['fully_paid'] is False
    assert data['payments'][0]['purpose'] == 'assistance_fee'
    assert data['payments'][0]['amount_inr'] == 30.0
