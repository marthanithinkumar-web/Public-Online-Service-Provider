import os
from ..utils.s3 import upload_file_to_s3
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from ..models.attachment import Attachment
from ..models.order import Order
from ..models.user import User
from ..utils.database import db
from ..utils.jwt_handler import decode_token
from datetime import datetime

bp = Blueprint('uploads', __name__)
ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def _auth():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    try:
        payload = decode_token(auth.split(' ', 1)[1])
        return User.query.get(payload.get('user_id'))
    except Exception:
        return None


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
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Invalid request.'}), 404
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'You are not authorized to upload to this request.'}), 403

    filename = secure_filename(f.filename)
    if not filename:
        return jsonify({'error': 'Invalid filename.'}), 400
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    stored_name = f"{timestamp}_{filename}"
    upload_folder = os.path.join(current_app.root_path, '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    local_path = os.path.join(upload_folder, stored_name)
    f.save(local_path)

    stored_path_value = local_path
    s3_bucket = os.getenv('S3_BUCKET')
    if s3_bucket:
        s3_key = f"attachments/{stored_name}"
        try:
            if upload_file_to_s3(local_path, s3_bucket, s3_key):
                stored_path_value = f"s3://{s3_bucket}/{s3_key}"
                try: os.remove(local_path)
                except OSError: pass
        except Exception:
            current_app.logger.exception('S3 upload failed')

    a = Attachment(order_id=order.id, filename=filename, stored_path=stored_path_value, uploaded_by=user.id)
    db.session.add(a)
    db.session.commit()
    return jsonify({'message': 'Document uploaded successfully.', 'attachment': {'id': a.id, 'order_id': a.order_id, 'filename': a.filename}}), 201


@bp.route('/<int:attachment_id>/download', methods=['GET'])
def download_attachment(attachment_id):
    user = _auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    a = Attachment.query.get_or_404(attachment_id)
    order = Order.query.get(a.order_id) if a.order_id else None
    if not user.is_admin and (not order or order.user_id != user.id):
        return jsonify({'error': 'Unauthorized'}), 403

    if a.stored_path and a.stored_path.startswith('s3://'):
        try:
            import boto3
            parts = a.stored_path.replace('s3://', '').split('/', 1)
            url = boto3.client('s3').generate_presigned_url('get_object', Params={'Bucket': parts[0], 'Key': parts[1]}, ExpiresIn=300)
            return jsonify({'url': url}), 200
        except Exception:
            current_app.logger.exception('Error generating presigned URL')
            return jsonify({'error': 'File not available'}), 500

    if not os.path.exists(a.stored_path):
        return jsonify({'error': 'File not found'}), 404
    return send_file(a.stored_path, as_attachment=True, download_name=a.filename)
