import os
from flask import Flask, jsonify
from dotenv import load_dotenv
from .utils.database import db
from .routes import auth, services, orders, admin, reviews, grievances, categories
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_talisman import Talisman
from flask_mail import Mail

load_dotenv()


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

    frontends = os.getenv('CORS_ORIGINS', os.getenv('FRONTEND_URL', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173'))
    allowed_origins = [origin.strip() for origin in frontends.split(',') if origin.strip()]
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

