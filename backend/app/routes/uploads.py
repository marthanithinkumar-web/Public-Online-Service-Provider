import os
from ..utils.s3 import presigned_download, upload_file_to_s3
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from ..models.attachment import Attachment
from ..models.order import Order
from ..models.user import User
from ..models.order_history import OrderStatusHistory
from ..models.notification import Notification
from ..utils.database import db
from ..utils.jwt_handler import get_request_user
from datetime import datetime, timezone

bp = Blueprint('uploads', __name__)
ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_REQUEST = 20
OPEN_UPLOAD_STATUSES = {'New', 'Submitted', 'Pending', 'Under Review', 'Documents Required', 'In Progress'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def _auth():
    return get_request_user()


def _matches_signature(filename, header):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return header.startswith(b'%PDF-')
    if ext == 'png':
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in {'jpg', 'jpeg'}:
        return header.startswith(b'\xff\xd8\xff')
    return False


@bp.route('/', methods=['POST'])
def upload_file():
    user = _auth()
    if not user:
        return jsonify({'error': 'Please log in to upload a document.'}), 401
    if 'file' not in request.files:
        return jsonify({'error': 'File is required.'}), 400

    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'Filename is empty.'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'Only PDF, PNG and JPG/JPEG documents are allowed.'}), 400
    if request.content_length and request.content_length > MAX_FILE_SIZE + 1024 * 1024:
        return jsonify({'error': 'File is too large. Maximum size is 10 MB.'}), 413

    order_id = request.form.get('order_id')
    if not order_id:
        return jsonify({'error': 'order_id is required.'}), 400
    try:
        order_id = int(order_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid request.'}), 400

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({'error': 'Invalid request.'}), 404
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'You are not authorized to upload to this request.'}), 403
    if order.status not in OPEN_UPLOAD_STATUSES:
        return jsonify({'error': 'Documents can no longer be uploaded because this request is closed.'}), 409
    if Attachment.query.filter_by(order_id=order.id).count() >= MAX_ATTACHMENTS_PER_REQUEST:
        return jsonify({'error': 'This request already has the maximum number of documents.'}), 400

    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename.'}), 400

    header = f.stream.read(16)
    f.stream.seek(0)
    if not _matches_signature(filename, header):
        return jsonify({'error': 'The uploaded file type does not match its filename.'}), 400

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    stored_name = f"{timestamp}_{filename}"
    upload_folder = os.path.join(current_app.root_path, '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    local_path = os.path.join(upload_folder, stored_name)
    f.save(local_path)

    try:
        if os.path.getsize(local_path) > MAX_FILE_SIZE:
            os.remove(local_path)
            return jsonify({'error': 'File is too large. Maximum size is 10 MB.'}), 413
    except OSError:
        return jsonify({'error': 'Unable to verify the uploaded file.'}), 500

    stored_path_value = local_path
    s3_bucket = os.getenv('S3_BUCKET')
    if s3_bucket:
        s3_key = f"attachments/{stored_name}"
        try:
            if not upload_file_to_s3(local_path, s3_bucket, s3_key):
                os.remove(local_path)
                return jsonify({'error': 'Persistent document storage is temporarily unavailable.'}), 503
            stored_path_value = f"s3://{s3_bucket}/{s3_key}"
            os.remove(local_path)
        except Exception:
            current_app.logger.exception('S3 upload failed')
            if os.path.exists(local_path):
                os.remove(local_path)
            return jsonify({'error': 'Persistent document storage is temporarily unavailable.'}), 503

    try:
        a = Attachment(order_id=order.id, filename=filename, stored_path=stored_path_value, uploaded_by=user.id)
        db.session.add(a)
        previous_status = order.status
        # A client response to Documents Required automatically returns the request to review.
        if not user.is_admin and order.status == 'Documents Required':
            order.status = 'Under Review'
        order.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.add(OrderStatusHistory(
            order_id=order.id,
            previous_status=previous_status,
            new_status=order.status,
            changed_by=user.email,
            note=(f'Document uploaded: {filename}' if previous_status == order.status else f'Document uploaded: {filename}. Request returned to Under Review.'),
        ))
        if user.is_admin and order.user_id:
            db.session.add(Notification(
                user_id=order.user_id,
                order_id=order.id,
                title='New document from the service team',
                message=f'A document is available for request {order.order_code}. Sign in to view or download it securely.',
            ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        if stored_path_value == local_path:
            try:
                os.remove(local_path)
            except OSError:
                pass
        raise

    message = 'Document delivered to the client successfully.' if user.is_admin else 'Document uploaded successfully.'
    return jsonify({'message': message, 'attachment': {'id': a.id, 'order_id': a.order_id, 'filename': a.filename}}), 201


@bp.route('/<int:attachment_id>/download', methods=['GET'])
def download_attachment(attachment_id):
    user = _auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    a = db.get_or_404(Attachment, attachment_id)
    order = db.session.get(Order, a.order_id) if a.order_id else None
    if not user.is_admin and (not order or order.user_id != user.id):
        return jsonify({'error': 'Unauthorized'}), 403

    if a.stored_path and a.stored_path.startswith('s3://'):
        try:
            parts = a.stored_path.replace('s3://', '').split('/', 1)
            url = presigned_download(parts[0], parts[1])
            return jsonify({'url': url}), 200
        except Exception:
            current_app.logger.exception('Error generating presigned URL')
            return jsonify({'error': 'File not available'}), 500

    if not os.path.exists(a.stored_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(a.stored_path, as_attachment=True, download_name=a.filename)
