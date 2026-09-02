from ..models.attachment import Attachment
from .database import db
from .s3 import delete_stored_file

CLIENT_DOCUMENT_PURGE_STATUSES = {'Completed', 'Rejected', 'Cancelled'}


def purge_client_documents_for_terminal_order(order) -> int:
    """Delete client-uploaded attachments before a terminal status is committed.

    Admin-delivered result documents are intentionally preserved. If private
    storage deletion fails, the caller's status transaction should fail rather
    than report the application as closed while retaining client documents.
    """
    if not order or order.status not in CLIENT_DOCUMENT_PURGE_STATUSES or not order.user_id:
        return 0
    attachments = Attachment.query.filter(
        Attachment.order_id == order.id,
        Attachment.uploaded_by == order.user_id,
    ).all()
    for attachment in attachments:
        delete_stored_file(attachment.stored_path)
        db.session.delete(attachment)
    return len(attachments)
