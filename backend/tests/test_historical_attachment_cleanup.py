from app.models.attachment import Attachment
from app.models.order import Order
from app.models.service import Category, Service
from app.models.user import User
from app.utils.attachment_retention import purge_historical_client_attachments
from app.utils.database import db


def _seed_legacy_closed_order(client, tmp_path):
    with client.application.app_context():
        client_user = User(
            email='legacy-retention-client@example.com',
            password_hash='test-hash',
            name='Legacy Retention Client',
            phone='9993030303',
        )
        admin_user = User(
            email='legacy-retention-admin@example.com',
            password_hash='test-hash',
            name='Legacy Retention Admin',
            is_admin=True,
        )
        category = Category(name='Legacy Retention Test')
        service = Service(
            name='Legacy Retention Service',
            description='Historical retention cleanup test service.',
            price_inr=30.0,
            category=category,
        )
        db.session.add_all([client_user, admin_user, service])
        db.session.flush()

        # Insert the order already closed to emulate a row that predates the
        # status-change purge hook. New closures are covered by the existing
        # attachment-retention regression tests.
        order = Order(
            order_code='POSP-LEGACY-RETENTION-1',
            client_name=client_user.name,
            phone=client_user.phone,
            email=client_user.email,
            service=service,
            user_id=client_user.id,
            status='Completed',
        )
        db.session.add(order)
        db.session.flush()

        client_path = tmp_path / 'legacy-client-proof.pdf'
        admin_path = tmp_path / 'legacy-result-document.pdf'
        client_path.write_bytes(b'legacy-client-document')
        admin_path.write_bytes(b'legacy-admin-result')

        client_attachment = Attachment(
            order_id=order.id,
            filename='legacy-client-proof.pdf',
            stored_path=str(client_path),
            uploaded_by=client_user.id,
        )
        admin_attachment = Attachment(
            order_id=order.id,
            filename='legacy-result-document.pdf',
            stored_path=str(admin_path),
            uploaded_by=admin_user.id,
        )
        db.session.add_all([client_attachment, admin_attachment])
        db.session.commit()

        return {
            'client_attachment_id': client_attachment.id,
            'admin_attachment_id': admin_attachment.id,
            'client_path': client_path,
            'admin_path': admin_path,
        }


def test_historical_cleanup_is_dry_run_by_default_and_preserves_admin_results(client, tmp_path):
    seeded = _seed_legacy_closed_order(client, tmp_path)

    with client.application.app_context():
        preview = purge_historical_client_attachments()
        assert preview['mode'] == 'dry-run'
        assert preview['matched_attachments'] == 1
        assert preview['matched_orders'] == 1
        assert preview['deleted_attachments'] == 0
        assert preview['failed_attachments'] == 0
        assert preview['status_counts'] == {'Completed': 1}
        assert db.session.get(Attachment, seeded['client_attachment_id']) is not None
        assert db.session.get(Attachment, seeded['admin_attachment_id']) is not None

    assert seeded['client_path'].exists()
    assert seeded['admin_path'].exists()

    with client.application.app_context():
        applied = purge_historical_client_attachments(apply=True)
        assert applied['mode'] == 'apply'
        assert applied['matched_attachments'] == 1
        assert applied['deleted_attachments'] == 1
        assert applied['failed_attachments'] == 0
        assert db.session.get(Attachment, seeded['client_attachment_id']) is None
        assert db.session.get(Attachment, seeded['admin_attachment_id']) is not None

    assert not seeded['client_path'].exists()
    assert seeded['admin_path'].exists()

    with client.application.app_context():
        repeated = purge_historical_client_attachments(apply=True)
        assert repeated['matched_attachments'] == 0
        assert repeated['deleted_attachments'] == 0
        assert repeated['failed_attachments'] == 0
