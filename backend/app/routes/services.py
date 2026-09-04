from flask import Blueprint, request, jsonify
from ..models.service import Service, Category, PlatformSetting
from ..utils.database import db
from ..middleware.auth import require_admin
from ..schemas.service_schema import ServiceSchema
from ..utils.service_requirements import get_service_requirements, SERVICE_REQUIREMENT_PROFILE_BY_NAME
from sqlalchemy import and_, or_
from ..utils.seo import application_service_name, legacy_application_service_name, slugify

bp = Blueprint('services', __name__)
schema = ServiceSchema()
RECHARGE_BILL_SERVICE_NAMES = (
    'Mobile Recharge',
    'Mobile Postpaid Bill Payment Assistance',
    'DTH Recharge Assistance',
    'Broadband / Landline Bill Payment Assistance',
    'FASTag Recharge Assistance',
    'Piped Gas Bill Payment Assistance',
)
for service_name in RECHARGE_BILL_SERVICE_NAMES:
    SERVICE_REQUIREMENT_PROFILE_BY_NAME[service_name] = 'utility'


def current_assistance_fee():
    setting = db.session.get(PlatformSetting, 'assistance_fee_inr')
    if setting:
        try:
            return max(0.0, float(setting.value))
        except (TypeError, ValueError):
            pass
    first = Service.query.filter(Service.price_inr.isnot(None)).order_by(Service.id.asc()).first()
    return float(first.price_inr) if first else 30.0


def homepage_assistance_fee():
    setting = db.session.get(PlatformSetting, 'homepage_assistance_fee_inr')
    if setting:
        try:
            value = float(setting.value)
            if value >= 0:
                return value
        except (TypeError, ValueError):
            pass
    return 30.0


def _fee_values(data, current=None):
    status = data.get('official_fee_status', getattr(current, 'official_fee_status', 'unconfirmed') or 'unconfirmed')
    amount = data.get('official_fee_inr', getattr(current, 'official_fee_inr', None))
    if status == 'known' and amount is None:
        raise ValueError('Official fee amount is required when its status is known.')
    if status == 'none':
        amount = 0.0
    elif status == 'unconfirmed':
        amount = None
    return status, amount


def _recharge_bill_requirements(service_name):
    fields_by_service = {
        'Mobile Recharge': [
            {'key': 'mobile_number', 'label': 'Mobile number', 'placeholder': '10-digit Indian mobile number', 'required': False},
            {'key': 'operator', 'label': 'Operator', 'type': 'select', 'options': ['Airtel', 'Jio', 'Vi', 'BSNL'], 'required': False},
            {'key': 'circle', 'label': 'Circle / state', 'placeholder': 'Mobile circle or state', 'required': False},
            {'key': 'plan_reference', 'label': 'Recharge plan', 'placeholder': 'Example: 28 days / 1.5 GB per day', 'required': False},
            {'key': 'recharge_amount', 'label': 'Recharge amount (₹)', 'placeholder': 'Plan amount', 'required': False},
        ],
        'Mobile Postpaid Bill Payment Assistance': [
            {'key': 'mobile_number', 'label': 'Postpaid mobile number', 'placeholder': '10-digit Indian mobile number', 'required': False},
            {'key': 'operator', 'label': 'Operator', 'type': 'select', 'options': ['Airtel', 'Jio', 'Vi', 'BSNL'], 'required': False},
            {'key': 'circle', 'label': 'Circle / state', 'placeholder': 'Mobile circle or state', 'required': False},
            {'key': 'account_reference', 'label': 'Account / customer reference (if available)', 'required': False},
            {'key': 'bill_amount', 'label': 'Bill amount (₹)', 'placeholder': 'Amount shown by the operator', 'required': False},
        ],
        'DTH Recharge Assistance': [
            {'key': 'dth_operator', 'label': 'DTH operator', 'type': 'select', 'options': ['Tata Play', 'Airtel Digital TV', 'Dish TV', 'd2h', 'Sun Direct', 'Other'], 'required': False},
            {'key': 'subscriber_id', 'label': 'Subscriber / customer ID', 'required': False},
            {'key': 'registered_mobile', 'label': 'Registered mobile number (if available)', 'required': False},
            {'key': 'plan_reference', 'label': 'Pack / plan reference (if known)', 'required': False},
            {'key': 'recharge_amount', 'label': 'Recharge amount (₹)', 'placeholder': 'Recharge amount', 'required': False},
        ],
        'Broadband / Landline Bill Payment Assistance': [
            {'key': 'provider', 'label': 'Broadband / landline provider', 'placeholder': 'Example: JioFiber, Airtel Xstream, BSNL, ACT', 'required': False},
            {'key': 'account_number', 'label': 'Account / customer number', 'required': False},
            {'key': 'landline_number', 'label': 'Landline / service number (if applicable)', 'required': False},
            {'key': 'circle', 'label': 'Circle / state / city', 'required': False},
            {'key': 'bill_amount', 'label': 'Bill amount (₹)', 'placeholder': 'Amount shown by the provider', 'required': False},
        ],
        'FASTag Recharge Assistance': [
            {'key': 'fastag_issuer', 'label': 'FASTag issuer / bank / provider', 'required': False},
            {'key': 'vehicle_registration', 'label': 'Vehicle registration number', 'required': False},
            {'key': 'fastag_reference', 'label': 'FASTag / customer reference (if available)', 'required': False},
            {'key': 'recharge_amount', 'label': 'Recharge amount (₹)', 'placeholder': 'Recharge amount', 'required': False},
        ],
        'Piped Gas Bill Payment Assistance': [
            {'key': 'provider', 'label': 'Piped gas provider', 'required': False},
            {'key': 'consumer_number', 'label': 'Consumer / customer number', 'required': False},
            {'key': 'location', 'label': 'City / state', 'required': False},
            {'key': 'bill_amount', 'label': 'Bill amount (₹)', 'placeholder': 'Amount shown by the gas provider', 'required': False},
        ],
    }
    return {
        'fields': fields_by_service[service_name],
        'documents': [],
        'safety_note': 'Never provide OTPs, UPI PINs, card PIN/CVV, banking passwords or provider-account passwords. The bill or recharge amount is separate from the website assistance fee, and the website does not claim third-party payment completion without an authorised provider integration.',
    }


def _service_dict(service):
    data = service.to_dict()
    data['requirements'] = _recharge_bill_requirements(service.name) if service.name in RECHARGE_BILL_SERVICE_NAMES else get_service_requirements(service)
    return data


def _catalog_response(services):
    response = jsonify([service.to_dict() for service in services])
    response.headers['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=300'
    return response


@bp.route('/', methods=['GET'])
@bp.route('', methods=['GET'])
def list_services():
    category_id = request.args.get('category_id')
    q = Service.query.filter_by(is_active=True)
    if category_id:
        try:
            q = q.filter_by(category_id=int(category_id))
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid category_id'}), 400
    services = q.order_by(Service.created_at.desc(), Service.name.asc()).all()
    return _catalog_response(services)


@bp.route('/homepage-assistance-fee', methods=['GET'])
def public_homepage_assistance_fee():
    response = jsonify({'price_inr': homepage_assistance_fee()})
    response.headers['Cache-Control'] = 'public, max-age=60, stale-while-revalidate=300'
    return response


@bp.route('/<int:service_id>', methods=['GET'])
def service_detail(service_id):
    s = Service.query.filter_by(id=service_id, is_active=True).first_or_404()
    return jsonify(_service_dict(s))


@bp.route('/by-slug/<string:service_slug>', methods=['GET'])
def service_detail_by_slug(service_slug):
    normalized = slugify(service_slug)
    legacy_slugs = {'aadhaar-pvc-card-order-guidance': 'aadhaar-pvc-card-order'}
    normalized = legacy_slugs.get(normalized, normalized)
    service = next((item for item in Service.query.filter_by(is_active=True).all() if normalized in {slugify(item.name), slugify(application_service_name(item.name)), slugify(legacy_application_service_name(item.name))}), None)
    if service is None:
        return jsonify({'error': 'Service not found'}), 404
    response = jsonify(_service_dict(service))
    response.headers['Cache-Control'] = 'public, max-age=300, stale-while-revalidate=3600'
    return response


@bp.route('/search', methods=['GET'])
def search():
    raw = (request.args.get('q') or '').strip()
    if not raw:
        services = Service.query.filter_by(is_active=True).order_by(Service.name.asc()).all()
        return _catalog_response(services)
    aliases = {'govt': 'government'}
    action_words = {'apply', 'application', 'applications', 'assistance', 'service', 'services'}
    tokens = [aliases.get(t.lower(), t) for t in raw.replace('-', ' ').replace('/', ' ').split() if t]
    search_terms = list(dict.fromkeys(term for term in tokens if term.lower() not in action_words))
    token_conditions = []
    for term in search_terms:
        pattern = f"%{term}%"
        token_conditions.append(or_(Service.name.ilike(pattern), Service.keywords.ilike(pattern), Service.description.ilike(pattern), Service.category.has(Category.name.ilike(pattern))))
    query = Service.query.filter(Service.is_active.is_(True))
    if token_conditions:
        query = query.filter(and_(*token_conditions))
    services = query.order_by(Service.name.asc()).limit(100).all()
    return _catalog_response(services)


@bp.route('/', methods=['POST'])
@require_admin
def create_service():
    data = request.json or {}
    errors = schema.validate(data)
    if errors:
        return jsonify({'error': errors}), 400
    try:
        official_status, official_amount = _fee_values(data)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    s = Service(name=data['name'], description=data.get('description'), price_inr=data.get('price_inr', current_assistance_fee()), official_fee_inr=official_amount, official_fee_status=official_status, keywords=data.get('keywords'), category_id=data.get('category_id'))
    db.session.add(s);db.session.commit()
    return jsonify({'message': 'Service created', 'service': _service_dict(s)})


@bp.route('/<int:service_id>', methods=['PUT'])
@require_admin
def update_service(service_id):
    s = db.get_or_404(Service, service_id);data = request.json or {};errors = schema.validate(data, partial=True)
    if errors:return jsonify({'error': errors}), 400
    try:official_status, official_amount = _fee_values(data, s)
    except ValueError as exc:return jsonify({'error': str(exc)}), 400
    s.name=data.get('name',s.name);s.description=data.get('description',s.description);s.price_inr=data.get('price_inr',s.price_inr);s.official_fee_status,s.official_fee_inr=official_status,official_amount;s.keywords=data.get('keywords',s.keywords);s.category_id=data.get('category_id',s.category_id);db.session.commit()
    return jsonify({'message':'Service updated','service':_service_dict(s)})


@bp.route('/<int:service_id>/active', methods=['POST'])
@require_admin
def set_service_active(service_id):
    s=db.get_or_404(Service,service_id);data=request.json or {};active=data.get('active')
    if active is None:return jsonify({'error':'active required (true/false)'}),400
    s.is_active=bool(active);db.session.commit();return jsonify({'message':'Service status updated','service':_service_dict(s)})
