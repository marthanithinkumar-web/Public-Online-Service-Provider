import os
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ..models.admin_audit import AdminAuditLog
from ..models.notification import Notification
from ..models.order import Order
from ..models.payment import Payment
from ..models.refund import Refund
from ..utils.database import db
from ..utils.jwt_handler import get_request_user
from ..utils.s3 import delete_stored_file, presigned_download, upload_file_to_s3

bp = Blueprint('refunds', __name__)
ALLOWED_METHODS = {'upi', 'bank_transfer', 'other'}
ALLOWED_EXT = {'pdf', 'png', 'jpg', 'jpeg'}
MAX_PROOF_SIZE = 10 * 1024 * 1024


def _paid_total_paise(order_id):
    payments = Payment.query.filter(
        Payment.order_id == order_id,
        Payment.status.in_(['captured', 'paid']),
    ).all()
    return sum(max(0, int(payment.amount_paise or 0)) for payment in payments)


def _summary(order_id):
    refunds = Refund.query.filter_by(order_id=order_id).order_by(Refund.refunded_at.asc(), Refund.id.asc()).all()
    paid_total = _paid_total_paise(order_id)
    refunded_total = sum(max(0, int(item.amount_paise or 0)) for item in refunds)
    status = 'not_refunded'
    if refunded_total > 0:
        status = 'refunded' if paid_total > 0 and refunded_total >= paid_total else 'partially_refunded'
    return refunds, paid_total, refunded_total, status


def _matches_signature(filename, header):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        return header.startswith(b'%PDF-')
    if ext == 'png':
        return header.startswith(b'\x89PNG\r\n\x1a\n')
    if ext in {'jpg', 'jpeg'}:
        return header.startswith(b'\xff\xd8\xff')
    return False


def _store_proof(file_obj, order_id):
    filename = secure_filename(file_obj.filename or '')
    if not filename or '.' not in filename or filename.rsplit('.', 1)[1].lower() not in ALLOWED_EXT:
        raise ValueError('Refund proof must be a PDF, PNG, JPG or JPEG file.')
    header = file_obj.stream.read(16)
    file_obj.stream.seek(0)
    if not _matches_signature(filename, header):
        raise ValueError('The refund proof file type does not match its filename.')
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    stored_name = f'refund_{order_id}_{timestamp}_{filename}'
    upload_folder = os.path.join(current_app.root_path, '..', '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    local_path = os.path.join(upload_folder, stored_name)
    file_obj.save(local_path)
    if os.path.getsize(local_path) > MAX_PROOF_SIZE:
        os.remove(local_path)
        raise ValueError('Refund proof is too large. Maximum size is 10 MB.')
    stored_path = local_path
    bucket = os.getenv('S3_BUCKET')
    if bucket:
        key = f'refund-proofs/{stored_name}'
        if not upload_file_to_s3(local_path, bucket, key):
            os.remove(local_path)
            raise RuntimeError('Persistent refund-proof storage is temporarily unavailable.')
        stored_path = f's3://{bucket}/{key}'
        os.remove(local_path)
    elif os.getenv('FLASK_ENV') == 'production' or os.getenv('FORCE_HTTPS') == '1':
        os.remove(local_path)
        raise RuntimeError('Persistent refund-proof storage is not configured.')
    return filename, stored_path


@bp.get('/order/<int:order_id>')
def order_refunds(order_id):
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    order = db.get_or_404(Order, order_id)
    if not user.is_admin and order.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    refunds, paid_total, refunded_total, status = _summary(order.id)
    return jsonify({
        'status': status,
        'paid_total_inr': round(paid_total / 100, 2),
        'refunded_total_inr': round(refunded_total / 100, 2),
        'remaining_refundable_inr': round(max(0, paid_total - refunded_total) / 100, 2),
        'refunds': [item.to_dict(include_private=user.is_admin) for item in refunds],
    })


@bp.post('/order/<int:order_id>')
def record_refund(order_id):
    admin = get_request_user()
    if not admin or not admin.is_admin:
        return jsonify({'error': 'Administrator access required.'}), 401
    order = Order.query.filter_by(id=order_id).with_for_update().first_or_404()
    if order.status != 'Cancelled':
        return jsonify({'error': 'Manual refunds can be recorded only after the application is cancelled.'}), 409
    try:
        amount_inr = round(float(request.form.get('amount_inr') or 0), 2)
    except (TypeError, ValueError):
        return jsonify({'error': 'Enter a valid refund amount.'}), 400
    if amount_inr <= 0 or amount_inr > 1000000:
        return jsonify({'error': 'Refund amount must be greater than ₹0.'}), 400
    amount_paise = int(round(amount_inr * 100))
    method = (request.form.get('method') or '').strip().lower()
    if method not in ALLOWED_METHODS:
        return jsonify({'error': 'Choose UPI, Bank Transfer, or Other as the refund method.'}), 400
    reference = (request.form.get('reference') or '').strip()
    if len(reference) < 3 or len(reference) > 160:
        return jsonify({'error': 'Enter the UTR, UPI transaction ID, or bank transaction reference.'}), 400
    duplicate = Refund.query.filter_by(order_id=order.id, reference=reference).first()
    if duplicate:
        return jsonify({'error': 'This refund transaction reference is already recorded for the application.'}), 409
    refunded_at_raw = (request.form.get('refunded_at') or '').strip()
    try:
        refunded_at = datetime.fromisoformat(refunded_at_raw).replace(tzinfo=None)
    except ValueError:
        return jsonify({'error': 'Refund date/time must be valid.'}), 400
    if refunded_at > datetime.now(timezone.utc).replace(tzinfo=None):
        return jsonify({'error': 'Refund date/time cannot be in the future.'}), 400
    note = (request.form.get('note') or '').strip()[:2000] or None
    refunds, paid_total, refunded_total, _ = _summary(order.id)
    remaining = max(0, paid_total - refunded_total)
    if paid_total <= 0:
        return jsonify({'error': 'No completed client payment is recorded for this application.'}), 409
    if amount_paise > remaining:
        return jsonify({'error': f'Refund exceeds the remaining refundable amount of ₹{remaining / 100:.2f}.'}), 409

    proof_filename = None
    proof_stored_path = None
    proof = request.files.get('proof')
    if proof and proof.filename:
        try:
            proof_filename, proof_stored_path = _store_proof(proof, order.id)
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({'error': str(exc)}), 503
        except Exception:
            current_app.logger.exception('Unable to store refund proof')
            return jsonify({'error': 'Unable to store the refund proof.'}), 500

    refund = Refund(
        order_id=order.id,
        amount_paise=amount_paise,
        method=method,
        reference=reference,
        refunded_at=refunded_at,
        note=note,
        proof_filename=proof_filename,
        proof_stored_path=proof_stored_path,
        recorded_by=admin.id,
    )
    try:
        db.session.add(refund)
        db.session.flush()
        new_refunded_total = refunded_total + amount_paise
        new_status = 'refunded' if new_refunded_total >= paid_total else 'partially_refunded'
        if order.user_id:
            db.session.add(Notification(
                user_id=order.user_id,
                order_id=order.id,
                title='Refund recorded',
                message=f'A manual refund of ₹{amount_inr:.2f} was recorded for request {order.order_code}. Method: {method.replace("_", " ").title()}. Transaction reference: {reference}.',
            ))
        db.session.add(AdminAuditLog(
            admin_id=admin.id,
            action='manual_refund_recorded',
            summary=f'Recorded ₹{amount_inr:.2f} manual refund for {order.order_code}.',
            details={'order_id': order.id, 'refund_id': refund.id, 'method': method, 'reference': reference, 'status': new_status},
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        if proof_stored_path:
            try:
                delete_stored_file(proof_stored_path)
            except Exception:
                current_app.logger.exception('Unable to clean up refund proof after database failure')
        raise
    return jsonify({'message': 'Refund recorded successfully.', 'refund': refund.to_dict(include_private=True)}), 201


@bp.get('/<int:refund_id>/proof')
def refund_proof(refund_id):
    user = get_request_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    refund = db.get_or_404(Refund, refund_id)
    order = db.session.get(Order, refund.order_id)
    if not user.is_admin and (not order or order.user_id != user.id):
        return jsonify({'error': 'Unauthorized'}), 403
    if not refund.proof_stored_path:
        return jsonify({'error': 'No refund proof was uploaded.'}), 404
    if refund.proof_stored_path.startswith('s3://'):
        try:
            bucket, key = refund.proof_stored_path.replace('s3://', '').split('/', 1)
            return jsonify({'url': presigned_download(bucket, key)}), 200
        except Exception:
            current_app.logger.exception('Unable to create refund-proof download link')
            return jsonify({'error': 'Refund proof is temporarily unavailable.'}), 500
    if not os.path.exists(refund.proof_stored_path):
        return jsonify({'error': 'Refund proof file was not found.'}), 404
    return send_file(refund.proof_stored_path, as_attachment=True, download_name=refund.proof_filename or 'refund-proof')
