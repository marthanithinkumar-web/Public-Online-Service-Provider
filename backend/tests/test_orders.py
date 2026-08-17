from app.main import create_app
from app.utils.database import db
from app.models.user import User
from app.utils.password import hash_password


def setup_test_app():
    app = create_app()
    app.config['TESTING'] = True
    return app


def test_order_creation_and_admin_status():
    app = setup_test_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        # create admin
        admin = User(email='admin@example.com', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
        client = app.test_client()
        # create a category and service
        from app.models.service import Category, Service
        c = Category(name='Certificates')
        db.session.add(c)
        db.session.commit()
        s = Service(name='Residence Certificate', description='Test', price_inr=30.0, category_id=c.id)
        db.session.add(s)
        db.session.commit()
        # create order
        r = client.post('/api/orders/', json={'client_name':'Alice','phone':'999','service_id':s.id})
        assert r.status_code == 200
        data = r.get_json()
        assert 'order' in data
        order_id = data['order']['id']
        # login admin
        r2 = client.post('/api/auth/login', json={'email':'admin@example.com','password':'adminpass'})
        assert r2.status_code == 200
        token = r2.get_json()['token']
        # update status
        r3 = client.post(f'/api/admin/orders/{order_id}/status', json={'status':'In Progress'}, headers={'Authorization':f'Bearer {token}'})
        assert r3.status_code == 200
        d3 = r3.get_json()
        assert d3['order']['status'] == 'In Progress'
