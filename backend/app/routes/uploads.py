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

# Allowed extensions for uploads
ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


@bp.route('/', methods=['POST'])
def upload_file():
    # Multipart form: file, order_id (optional), order_code+phone optional
    if 'file' not in request.files:
        return jsonify({'error': 'file required'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'filename empty'}), 400

    if not allowed_file(f.filename):
        return jsonify({'error': 'file type not allowed'}), 400

    # authorization: either admin/user via Bearer token or order_code+phone matching
    auth = request.headers.get('Authorization', '')
    user_id = None
    is_admin = False
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('user_id')
            is_admin = payload.get('is_admin', False)
        except Exception:
            user_id = None

    order_id = request.form.get('order_id')
    order_code = request.form.get('order_code')
    phone = request.form.get('phone')

    order = None
    if order_id:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Invalid order_id'}), 400
        # if user is not admin and order has a user_id, ensure matches
        if not is_admin and order.user_id and user_id != order.user_id:
            return jsonify({'error': 'Unauthorized for this order'}), 401
    else:
        # try identify order by order_code+phone
        if order_code and phone:
            order = Order.query.filter_by(order_code=order_code, phone=phone).first()
        if not order and not is_admin and not user_id:
            return jsonify({'error': 'order_id or valid order_code+phone or auth required'}), 401

    # safe filename
    filename = secure_filename(f.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    stored_name = f"{timestamp}_{filename}"
    upload_folder = os.path.join(current_app.root_path, '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    local_path = os.path.join(upload_folder, stored_name)

    # save file locally first
    f.save(local_path)

    stored_path_value = local_path

    # if S3 is configured, try to upload and remove local copy
    s3_bucket = os.getenv('S3_BUCKET')
    if s3_bucket:
        s3_key = f"attachments/{stored_name}"
        try:
            uploaded = upload_file_to_s3(local_path, s3_bucket, s3_key)
            if uploaded:
                # store s3 path and remove local file
                stored_path_value = f"s3://{s3_bucket}/{s3_key}"
                try:
                    os.remove(local_path)
                except Exception:
                    current_app.logger.debug('Could not remove local uploaded file')
        except Exception as e:
            current_app.logger.exception('S3 upload failed: %s', e)

    a = Attachment(
        order_id=order.id if order else None,
        filename=filename,
        stored_path=stored_path_value,
        uploaded_by=user_id
    )
    db.session.add(a)
    db.session.commit()

    return jsonify({'message': 'File uploaded', 'attachment': {
        'id': a.id, 'order_id': a.order_id, 'filename': a.filename
    }})


@bp.route('/<int:attachment_id>/download', methods=['GET'])
def download_attachment(attachment_id):
    auth = request.headers.get('Authorization', '')
    user_id = None
    is_admin = False
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            payload = decode_token(token)
            user_id = payload.get('user_id')
            is_admin = payload.get('is_admin', False)
        except Exception:
            user_id = None

    a = Attachment.query.get_or_404(attachment_id)
    # check access: admin, uploader, or order owner (or order_code+phone if provided)
    if not is_admin:
        allowed = False
        if a.uploaded_by and user_id and a.uploaded_by == user_id:
            allowed = True
        if a.order_id:
            order = Order.query.get(a.order_id)
            if order and order.user_id and user_id and order.user_id == user_id:
                allowed = True
            # allow order_code+phone query param to access when not authenticated
            if not user_id:
                oc = request.args.get('order_code')
                ph = request.args.get('phone')
                if oc and ph and order and order.order_code == oc and order.phone == ph:
                    allowed = True
        if not allowed:
            return jsonify({'error': 'Unauthorized'}), 401

    # if stored on S3, return a presigned URL (requires boto3)
    if a.stored_path and a.stored_path.startswith('s3://'):
        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError
            # parse
            parts = a.stored_path.replace('s3://', '').split('/', 1)
            bucket = parts[0]
            key = parts[1]
            s3 = boto3.client('s3')
            url = s3.generate_presigned_url('get_object', Params={'Bucket': bucket, 'Key': key}, ExpiresIn=300)
            return jsonify({'url': url}), 200
        except Exception as e:
            current_app.logger.exception('Error generating presigned URL: %s', e)
            return jsonify({'error': 'File not available'}), 500

    # ensure local file exists
    if not os.path.exists(a.stored_path):
        return jsonify({'error': 'File not found'}), 404

    return send_file(a.stored_path, as_attachment=True, download_name=a.filename)
