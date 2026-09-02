import os
from io import BytesIO

from app.models.attachment import Attachment
from app.models.service import Category, Service
from app.models.user import User
from app.utils.database import db
from app.utils.password import hash_password


def _service_id(client):
    with client.application.app_context():
        category = Category.query.filter_by(name='Certificates').first()
        if category is None:
            category = Category(name='Certificates')
            db.session.add(category)
            db.session.flush()
        service = Service.query.filter_by(name='Retention Test Service').first()
        if service is None:
            service = Service(
                name='Retention Test Service',
                description='Attachment retention test service',
                price_inr=30.0,
                category=category,
            )
            db.session.add(service)
            db.session.commit()
        return service.id


def _register_client(client, email, phone):
    response = client.post('/api/auth/register', json={
        'name': 'Retention Client',
        'phone': phone,
        'email': email,
        'password': 'strong-pass1',
    })
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def _admin_headers(client):
    with client.application.app_context():
        admin = User(email='retention-admin@example.com', password_hash=hash_password('adminpass'), is_admin=True)
        db.session.add(admin)
        db.session.commit()
    response = client.post('/api/auth/login', json={'email': 'retention-admin@example.com', 'password': 'adminpass'})
    assert response.status_code == 200
    return {'Authorization': f"Bearer {response.get_json()['token']}"}


def _create_order(client, headers, service_id, purpose):
    response = client.post('/api/orders/', json={
        'service_id': service_id,
        'application_data': {'purpose': purpose},
        'contact_method': 'phone',
    }, headers=headers)
    assert response.status_code == 201
    return response.get_json()['order']['id']


def _upload_png(client, headers, order_id, filename):
    response = client.post(
        '/api/uploads/',
        data={'order_id': str(order_id), 'file': (BytesIO(b'\x89PNG\r\n\x1a\nretention-test'), filename)},
        headers=headers,
        content_type='multipart/form-data',
    )
    assert response.status_code == 201
    return response.get_json()['attachment']['id']


def test_client_documents_are_purged_when_admin_completes_application(client):
    service_id = _service_id(client)
    client_headers = _register_client(client, 'retention-client@example.com', '9991010101')
    admin_headers = _admin_headers(client)
    order_id = _create_order(client, client_headers, service_id, 'completion')

    client_attachment_id = _upload_png(client, client_headers, order_id, 'client-proof.png')
    admin_attachment_id = _upload_png(client, admin_headers, order_id, 'result-document.png')

    with client.application.app_context():
        client_path = db.session.get(Attachment, client_attachment_id).stored_path
        admin_path = db.session.get(Attachment, admin_attachment_id).stored_path
        assert os.path.exists(client_path)
        assert os.path.exists(admin_path)

    assert client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'Under Review'}, headers=admin_headers).status_code == 200
    assert client.post(f'/api/admin/orders/{order_id}/status', json={'status': 'In Progress', 'note': 'Processing.'}, headers=admin_headers).status_code == 200
    completed = client.post(
        f'/api/admin/orders/{order_id}/status',
        json={'status': 'Completed', 'note': 'Completed and result delivered.'},
        headers=admin_headers,
    )
    assert completed.status_code == 200

    with client.application.app_context():
        assert db.session.get(Attachment, client_attachment_id) is None
        assert db.session.get(Attachment, admin_attachment_id) is not None
        assert not os.path.exists(client_path)
        assert os.path.exists(admin_path)

    detail = client.get(f'/api/admin/orders/{order_id}', headers=admin_headers).get_json()
    assert [item['id'] for item in detail['attachments']] == [admin_attachment_id]
    assert client.get(f'/api/uploads/{client_attachment_id}/download', headers=admin_headers).status_code == 404
    assert client.get(f'/api/uploads/{admin_attachment_id}/download', headers=admin_headers).status_code == 200


def test_client_documents_are_purged_when_client_withdraws_application(client):
    service_id = _service_id(client)
    client_headers = _register_client(client, 'withdraw-client@example.com', '9992020202')
    order_id = _create_order(client, client_headers, service_id, 'withdrawal')
    attachment_id = _upload_png(client, client_headers, order_id, 'withdraw-proof.png')

    with client.application.app_context():
        stored_path = db.session.get(Attachment, attachment_id).stored_path
        assert os.path.exists(stored_path)

    cancelled = client.post(
        f'/api/orders/{order_id}/cancel',
        json={'reason': 'Client withdrew the application.'},
        headers=client_headers,
    )
    assert cancelled.status_code == 200

    with client.application.app_context():
        assert db.session.get(Attachment, attachment_id) is None
        assert not os.path.exists(stored_path)

    detail = client.get(f'/api/orders/{order_id}', headers=client_headers).get_json()
    assert detail['order']['status'] == 'Cancelled'
    assert detail['attachments'] == []
    assert client.get(f'/api/uploads/{attachment_id}/download', headers=client_headers).status_code == 404
