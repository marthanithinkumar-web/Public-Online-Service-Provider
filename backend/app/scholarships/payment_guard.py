from flask import jsonify, request

from ..models.order import Order

SCHOLARSHIP_SERVICE_NAME = 'Scholarship Application Assistance'


def register_scholarship_payment_guard(app):
    """Keep scholarship requests assistance-only even if a client calls payment APIs directly."""
    @app.before_request
    def scholarship_payment_guard():
        if request.method != 'POST':
            return None
        prefix = '/api/payments/orders/'
        suffix = '/checkout'
        if not request.path.startswith(prefix) or not request.path.endswith(suffix):
            return None
        raw_order_id = request.path[len(prefix):-len(suffix)]
        if not raw_order_id.isdigit():
            return None
        order = Order.query.filter_by(id=int(raw_order_id)).first()
        if not order or not order.service or order.service.name != SCHOLARSHIP_SERVICE_NAME:
            return None
        data = request.get_json(silent=True) or {}
        purpose = str(data.get('purpose') or 'assistance_fee').strip()
        if purpose != 'assistance_fee':
            return jsonify({
                'error': 'Scholarship requests accept only the application assistance fee. There is no official-fee or combined-fee payment option.'
            }), 409
        return None
