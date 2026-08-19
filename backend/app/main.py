import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from .utils.database import db
from .models.user import User
from .models.service import Category, Service
from .routes import auth, services, orders, admin, reviews, grievances, categories
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_mail import Mail
from .utils.password import hash_password, verify_password

load_dotenv()


def ensure_admin_user():
    admin_email = (os.getenv('ADMIN_EMAIL') or '').strip().lower()
    admin_password = os.getenv('ADMIN_PASSWORD')
    if not admin_email or not admin_password:
        return

    user = User.query.filter_by(email=admin_email).first()
    if user is None:
        user = User(email=admin_email, password_hash=hash_password(admin_password), is_admin=True)
        db.session.add(user)
        db.session.commit()
        return

    needs_update = False
    if not user.is_admin:
        user.is_admin = True
        needs_update = True
    if not verify_password(admin_password, user.password_hash):
        user.password_hash = hash_password(admin_password)
        needs_update = True

    if needs_update:
        db.session.commit()


def ensure_default_services():
    """Ensure the production database has the public services used by the UI.

    This is intentionally idempotent: existing categories/services are preserved,
    while missing defaults are added. It also repairs the previous seed behavior
    that only inserted services when the first category was missing.
    """
    defaults = [
        {
            'category': 'Certificates',
            'name': 'Residence Certificate',
            'description': 'Assistance to apply for residence/domicile certificate',
            'price_inr': 30.0,
            'keywords': 'residence,domicile,address,certificate',
        },
        {
            'category': 'Certificates',
            'name': 'Ration Card Services',
            'description': 'Help with Ration Card related applications',
            'price_inr': 50.0,
            'keywords': 'ration,card,food,subsidy',
        },
        {
            'category': 'Government Jobs',
            'name': 'Government Job Application',
            'description': 'Assistance to apply for government job openings',
            'price_inr': 100.0,
            'keywords': 'job,application,recruitment,jobs',
        },
        {
            'category': 'Scholarships',
            'name': 'Scholarship Application Assistance',
            'description': 'Guidance and application support for eligible scholarships',
            'price_inr': 50.0,
            'keywords': 'scholarship,education,student,financial aid',
        },
        {
            'category': 'MeeSeva / Public Services',
            'name': 'MeeSeva Service Assistance',
            'description': 'Assistance with common MeeSeva and public service applications',
            'price_inr': 50.0,
            'keywords': 'meeseva,public service,government,application',
        },
        {
            'category': 'Government Schemes',
            'name': 'Government Scheme Application Support',
            'description': 'Eligibility guidance and application assistance for government schemes',
            'price_inr': 50.0,
            'keywords': 'scheme,government scheme,benefit,eligibility',
        },
    ]

    categories_by_name = {}
    for item in defaults:
        category_name = item['category']
        category = Category.query.filter_by(name=category_name).first()
        if category is None:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        categories_by_name[category_name] = category

    for item in defaults:
        category = categories_by_name[item['category']]
        service = Service.query.filter_by(name=item['name']).first()
        if service is None:
            db.session.add(
                Service(
                    name=item['name'],
                    description=item['description'],
                    price_inr=item['price_inr'],
                    keywords=item['keywords'],
                    category_id=category.id,
                    is_active=True,
                )
            )
        else:
            # A default service should remain searchable if an earlier deployment
            # created it without the expected active flag or category association.
            changed = False
            if not service.is_active:
                service.is_active = True
                changed = True
            if service.category_id is None:
                service.category_id = category.id
                changed = True
            if changed:
                db.session.add(service)

    db.session.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///psp.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.getenv('SMTP_HOST', ''),
        MAIL_PORT=int(os.getenv('SMTP_PORT') or 0),
        MAIL_USERNAME=os.getenv('SMTP_USER'),
        MAIL_PASSWORD=os.getenv('SMTP_PASS'),
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
    )

    # security headers - do not force HTTPS redirects by default in dev/test.
    # Set FORCE_HTTPS=1 in environment to enable strict HTTPS redirects in production.
    force_https = os.getenv('FORCE_HTTPS', '0') == '1'
    Talisman(app, content_security_policy=None, force_https=force_https)

    db.init_app(app)

    # Keep explicit CORS configuration for production, while also including the
    # known Render UI origin so a missing/incorrect FRONTEND_URL cannot silently
    # break public read-only endpoints such as service search.
    configured_origins = os.getenv('CORS_ORIGINS')
    if configured_origins:
        frontends = configured_origins
    else:
        frontends = os.getenv(
            'FRONTEND_URL',
            'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173'
        )
    allowed_origins = [origin.strip().rstrip('/') for origin in frontends.split(',') if origin.strip()]
    render_ui_origin = 'https://public-online-service-provider-ui.onrender.com'
    if render_ui_origin not in allowed_origins:
        allowed_origins.append(render_ui_origin)
    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS']
    )

    # migrations
    migrate = Migrate(app, db)

    # rate limiter (configured globally in utils.limiter)
    from .utils.limiter import limiter
    limiter._default_limits = ["2000 per day", "500 per hour"]
    limiter.init_app(app)

    # mail
    mail = Mail(app)

    # limit uploads to reasonable size (default 5MB)
    app.config.setdefault('MAX_CONTENT_LENGTH', int(os.getenv('MAX_UPLOAD_MB', '5')) * 1024 * 1024)

    with app.app_context():
        db.create_all()
        ensure_default_services()
        ensure_admin_user()

    # register blueprints
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(services.bp, url_prefix='/api/services')
    app.register_blueprint(orders.bp, url_prefix='/api/orders')
    app.register_blueprint(admin.bp, url_prefix='/api/admin')
    app.register_blueprint(reviews.bp, url_prefix='/api/reviews')
    app.register_blueprint(grievances.bp, url_prefix='/api/grievances')
    app.register_blueprint(categories.bp, url_prefix='/api/categories')
    app.register_blueprint(__import__('app.routes.uploads', fromlist=['bp']).bp, url_prefix='/api/uploads')

    @app.get('/')
    def index():
        return jsonify({"message": "Public Online Service Provider API"})

    return app
