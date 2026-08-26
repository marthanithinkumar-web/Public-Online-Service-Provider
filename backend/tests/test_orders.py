from app.main import create_app
from app.utils.database import db
from app.utils.password import hash_password
from app.models.user import User


def test_complete_request_lifecycle(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f'sqlite:///{tmp_path / "lifecycle.db"}')
    app=create_app();app.config['TESTING']=True
    with app.app_context():
        db.drop_all();db.create_all()
        admin=User(email='admin@example.com',password_hash=hash_password('adminpass'),is_admin=True);db.session.add(admin);db.session.commit()
        from app.models.service import Category,Service
        c=Category(name='Certificates');db.session.add(c);db.session.commit();s=Service(name='Residence Certificate',description='Test',price_inr=30.0,official_fee_inr=120.0,official_fee_status='known',category_id=c.id);db.session.add(s);db.session.commit()
        client=app.test_client();r0=client.post('/api/auth/register',json={'name':'Alice','phone':'9990001111','email':'alice@example.com','password':'alicepass'});assert r0.status_code==200;client_token=r0.get_json()['token']
        r=client.post('/api/orders/',json={'service_id':s.id,'application_data':{'certificate_type':'Residence','purpose':'Official use'},'contact_method':'phone'},headers={'Authorization':f'Bearer {client_token}'});assert r.status_code==201;created=r.get_json()['order'];order_id=created['id'];assert created['fee_inr']==30.0;assert created['official_fee_inr']==120.0;assert created['official_fee_status']=='known';assert created['total_fee_inr']==150.0
        r2=client.post('/api/auth/login',json={'email':'admin@example.com','password':'adminpass'});assert r2.status_code==200;admin_token=r2.get_json()['token'];admin_headers={'Authorization':f'Bearer {admin_token}'}
        r3=client.post(f'/api/admin/orders/{order_id}/status',json={'status':'Under Review'},headers=admin_headers);assert r3.status_code==200
        r3=client.post(f'/api/admin/orders/{order_id}/status',json={'status':'In Progress','note':'Started processing.'},headers=admin_headers);assert r3.status_code==200
        r3=client.post(f'/api/admin/orders/{order_id}/status',json={'status':'Completed','note':'Service completed and result delivered.'},headers=admin_headers);assert r3.status_code==200
        r4=client.post('/api/reviews',json={'order_id':order_id,'rating':5,'comment':'Excellent assistance.'},headers={'Authorization':f'Bearer {client_token}'});assert r4.status_code==201
        r5=client.post('/api/grievances',json={'order_id':order_id,'description':'I need clarification about the completed request.'},headers={'Authorization':f'Bearer {client_token}'});assert r5.status_code==201
