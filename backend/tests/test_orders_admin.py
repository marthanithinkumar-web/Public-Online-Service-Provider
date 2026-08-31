from app.utils.password import hash_password
from app.utils.database import db
from app.models.user import User
from app.models.service import Category, Service
from io import BytesIO


def test_order_lifecycle_and_admin_controls(client):
    with client.application.app_context():
        cat = Category.query.filter_by(name='Certificates').first()
        if cat is None:
            cat = Category(name='Certificates')
            db.session.add(cat)
            db.session.commit()
        svc = Service.query.filter_by(name='Residence Certificate').first()
        if svc is None:
            svc = Service(name='Residence Certificate', description='Residence proof', price_inr=30.0, category=cat)
            db.session.add(svc)
            db.session.commit()
        service_id = svc.id

    r = client.post('/api/auth/register', json={'name':'User One','phone':'9990001111','email': 'user1@example.com', 'password': 'strong-pass1'})
    assert r.status_code == 200
    token1 = r.get_json()['token']
    r = client.post('/api/auth/register', json={'name':'User Two','phone':'9990002222','email': 'user2@example.com', 'password': 'strong-pass2'})
    assert r.status_code == 200
    token2 = r.get_json()['token']
    headers1 = {'Authorization': f'Bearer {token1}'}
    headers2 = {'Authorization': f'Bearer {token2}'}

    application = {'certificate_type': 'Residence', 'purpose': 'Official use'}
    order_payload = {'service_id': service_id, 'application_data': application, 'contact_method': 'phone'}
    r = client.post('/api/orders/', json=order_payload, headers=headers1)
    assert r.status_code == 201
    order = r.get_json()['order']
    order_id = order['id']

    r = client.get(f'/api/orders/{order_id}', headers=headers2)
    assert r.status_code == 403
    r = client.get(f'/api/orders/{order_id}', headers=headers1)
    assert r.status_code == 200
    assert r.get_json()['order']['id'] == order_id

    r = client.post('/api/orders/', json=order_payload, headers=headers1)
    assert r.status_code == 200
    assert r.get_json()['duplicate'] is True
    assert r.get_json()['order']['id'] == order_id

    client_upload = client.post(
        '/api/uploads/',
        data={'order_id': str(order_id), 'file': (BytesIO(b'\x89PNG\r\n\x1a\nclient-test'), 'client-document.png')},
        headers=headers1,
        content_type='multipart/form-data',
    )
    assert client_upload.status_code == 201
    client_attachment_id = client_upload.get_json()['attachment']['id']
    assert client.delete(f'/api/uploads/{client_attachment_id}', headers=headers2).status_code == 403
    removed = client.delete(f'/api/uploads/{client_attachment_id}', headers=headers1)
    assert removed.status_code == 200
    assert client.get(f'/api/uploads/{client_attachment_id}/download', headers=headers1).status_code == 404

    with client.application.app_context():
        admin = User(email='admin@example.com', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()

    r = client.post('/api/auth/login', json={'email': 'admin@example.com', 'password': 'adminpass'})
    assert r.status_code == 200
    admin_token = r.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    r = client.get('/api/admin/orders', headers=admin_headers)
    assert r.status_code == 200
    assert any(it['id'] == order_id for it in r.get_json()['items'])

    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Under Review'}, headers=admin_headers)
    assert r.status_code == 200
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'In Progress', 'note': 'Started processing.'}, headers=admin_headers)
    assert r.status_code == 200

    delivered = client.post(
        '/api/uploads/',
        data={'order_id': str(order_id), 'file': (BytesIO(b'%PDF-1.4\n%%EOF'), 'official-document.pdf')},
        headers=admin_headers,
        content_type='multipart/form-data',
    )
    assert delivered.status_code == 201
    assert 'delivered to the client' in delivered.get_json()['message']
    attachment_id = delivered.get_json()['attachment']['id']
    client_detail = client.get(f'/api/orders/{order_id}', headers=headers1).get_json()
    attachment = next(item for item in client_detail['attachments'] if item['id'] == attachment_id)
    assert attachment['uploaded_by_role'] == 'admin'
    assert 'uploaded_by' not in attachment
    assert any(item['title'] == 'New document from the service team' for item in client_detail['notifications'])
    assert client.get(f'/api/uploads/{attachment_id}/download', headers=headers1).status_code == 200
    assert client.get(f'/api/uploads/{attachment_id}/download', headers=headers2).status_code == 403
    assert client.delete(f'/api/uploads/{attachment_id}', headers=headers1).status_code == 403
    assert client.delete(f'/api/uploads/{attachment_id}', headers=admin_headers).status_code == 200
    assert client.get(f'/api/uploads/{attachment_id}/download', headers=headers1).status_code == 404

    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'New'}, headers=admin_headers)
    assert r.status_code == 409

    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Completed'}, headers=admin_headers)
    assert r.status_code == 400
    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Completed', 'note': 'Service completed and result delivered.'}, headers=admin_headers)
    assert r.status_code == 200

    r = client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Cancelled', 'note': 'No longer needed.'}, headers=admin_headers)
    assert r.status_code == 409

    r = client.get(f'/api/admin/orders/{order_id}', headers=admin_headers)
    assert r.status_code == 200
    detail = r.get_json()
    assert detail['order']['id'] == order_id
    assert detail['order']['status'] == 'Completed'
    assert detail['allowed_next_statuses'] == []
    assert len(detail['history']) >= 4
