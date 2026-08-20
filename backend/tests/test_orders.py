from app.main import create_app
from app.utils.database import db
from app.utils.password import hash_password
from app.models.user import User


def test_complete_request_lifecycle():
    app=create_app();app.config['TESTING']=True
    with app.app_context():
        db.drop_all();db.create_all()
        admin=User(email='admin@example.com',password_hash=hash_password('adminpass'),is_admin=True);db.session.add(admin);db.session.commit()
        from app.models.service import Category,Service
        c=Category(name='Certificates');db.session.add(c);db.session.commit();s=Service(name='Residence Certificate',description='Test',price_inr=30.0,category_id=c.id);db.session.add(s);db.session.commit()
        client=app.test_client();r0=client.post('/api/auth/register',json={'name':'Alice','phone':'9990001111','email':'alice@example.com','password':'alicepass'});assert r0.status_code==200;client_token=r0.get_json()['token']
        r=client.post('/api/orders/',json={'client_name':'Alice','phone':'9990001111','service_id':s.id,'application_data':{'certificate_type':'Residence','purpose':'Official use'}},headers={'Authorization':f'Bearer {client_token}'});assert r.status_code==201;order_id=r.get_json()['order']['id']
        r2=client.post('/api/auth/login',json={'email':'admin@example.com','password':'adminpass'});assert r2.status_code==200;admin_token=r2.get_json()['token']
        for status in ('Under Review','In Progress','Completed'):
            r3=client.post(f'/api/admin/orders/{order_id}/status',json={'status':status},headers={'Authorization':f'Bearer {admin_token}'});assert r3.status_code==200
        r4=client.post('/api/reviews',json={'order_id':order_id,'rating':5,'comment':'Excellent assistance.'},headers={'Authorization':f'Bearer {client_token}'});assert r4.status_code==201
        r5=client.post('/api/grievances',json={'order_id':order_id,'description':'I need clarification about the completed request.'},headers={'Authorization':f'Bearer {client_token}'});assert r5.status_code==201
