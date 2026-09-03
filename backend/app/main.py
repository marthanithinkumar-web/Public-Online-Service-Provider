import os
from flask import Flask, jsonify
from sqlalchemy import text
from dotenv import load_dotenv
from .utils.database import db
from .utils.schema_compat import ensure_user_schema
from .models.user import User
from .models.service import Category, Service
from .models.job import JobSource
from .models.payment import Payment
from .routes import auth, services, orders, admin, reviews, grievances, categories, notifications, messages, jobs, fees, payments, admin_payments, scholarships
from flask_cors import CORS
from flask_migrate import Migrate
from flask_talisman import Talisman
from .utils.password import hash_password

load_dotenv()

def validate_runtime_security():
    if os.getenv('FLASK_ENV') != 'production':
        return
    secret = (os.getenv('SECRET_KEY') or '').strip()
    if len(secret) < 32 or secret in {'dev-key', 'change-me-to-a-secure-random-string'}:
        raise RuntimeError('Production requires a unique SECRET_KEY of at least 32 characters.')

def database_engine_options(uri):
    options={'pool_pre_ping':True,'pool_recycle':280}
    if uri.startswith(('postgresql://','postgres://')):
        options.update(pool_size=max(1,int(os.getenv('DB_POOL_SIZE','5'))),max_overflow=max(0,int(os.getenv('DB_MAX_OVERFLOW','5'))),pool_timeout=max(5,int(os.getenv('DB_POOL_TIMEOUT','20'))),connect_args={'connect_timeout':max(3,int(os.getenv('DB_CONNECT_TIMEOUT','10'))),'options':'-c statement_timeout='+str(max(1000,int(os.getenv('DB_STATEMENT_TIMEOUT_MS','20000'))))})
    return options

def ensure_admin_user():
    admin_email=(os.getenv('ADMIN_EMAIL') or '').strip().lower();admin_password=os.getenv('ADMIN_PASSWORD')
    if not admin_email or not admin_password:return
    user=User.query.filter_by(email=admin_email).first()
    if user is None:db.session.add(User(email=admin_email,password_hash=hash_password(admin_password),is_admin=True));db.session.commit();return
    changed=False
    if not user.is_admin:user.is_admin=True;changed=True
    if changed:db.session.commit()

def ensure_default_services():
    defaults=[('Certificates','Residence Certificate','Assistance to apply for residence/domicile certificate',30.0,'residence,domicile,address,certificate'),('Certificates','Ration Card Services','Help with Ration Card related applications',30.0,'ration,card,food,subsidy'),('Government Jobs','Government Job Application','Assistance to apply for government job openings',30.0,'job,application,recruitment,jobs'),('Scholarships','Scholarship Application Assistance','Guidance and application support for eligible scholarships',30.0,'scholarship,education,student,financial aid'),('MeeSeva / Public Services','MeeSeva Service Assistance','Assistance with common MeeSeva and public service applications',30.0,'meeseva,public service,government,application'),('Government Schemes','Government Scheme Application Support','Eligibility guidance and application assistance for government schemes',30.0,'scheme,government scheme,benefit,eligibility'),('Travel & Ticketing Assistance','Railway Ticket Booking Assistance','Guidance for railway ticket search and booking through the official railway process. Clients complete OTP and payment directly on the official portal.',30.0,'railway,train,ticket,tickets,booking,irctc,travel'),('Identity & Citizen Documents','Official Document PDF Access Assistance','Help clients access an available official PDF or digital copy through the relevant official portal. This service does not create, alter or replace an identity document; clients complete any OTP or portal authentication themselves.',5.0,'pdf,document pdf,digital copy,download,aadhaar,aadhar,e-aadhaar,voter id,e-epic,pan,e-pan,abha,apaar,digilocker,ration card,driving licence,rc,certificate,marksheet')]
    defaults.extend([('Travel & Ticketing Assistance','Student Bus Pass Assistance','Help with a student bus-pass application or renewal.',30.0,'bus pass,student bus pass,concession pass,tgsrtc,tsrtc,apsrtc,renewal'),('Travel & Ticketing Assistance','General Bus Pass Assistance','Help with a general commuter bus-pass application or renewal.',30.0,'bus pass,general bus pass,commuter pass,tgsrtc,tsrtc,apsrtc,renewal')])
    for cat_name,name,desc,price,keywords in defaults:
        cat=Category.query.filter_by(name=cat_name).first()
        if cat is None:cat=Category(name=cat_name);db.session.add(cat);db.session.flush()
        service=Service.query.filter_by(name=name).first()
        if service is None:db.session.add(Service(name=name,description=desc,price_inr=price,keywords=keywords,category_id=cat.id,is_active=True))
        else:service.category_id=service.category_id or cat.id
    residence=Service.query.filter_by(name='Residence Certificate').first()
    if residence:residence.official_fee_status='known';residence.official_fee_inr=80.0
    db.session.commit()

def ensure_job_sources():
    from .jobs.sync import ensure_job_sources as ensure_sources
    ensure_sources()

def create_app():
    validate_runtime_security()
    database_uri=os.getenv('DATABASE_URL','sqlite:///psp.db')
    app=Flask(__name__);app.config.from_mapping(SECRET_KEY=os.getenv('SECRET_KEY','dev-key'),SQLALCHEMY_DATABASE_URI=database_uri,SQLALCHEMY_TRACK_MODIFICATIONS=False,SQLALCHEMY_ENGINE_OPTIONS=database_engine_options(database_uri),MAIL_SERVER=os.getenv('SMTP_HOST',''),MAIL_PORT=int(os.getenv('SMTP_PORT') or 0),MAIL_USERNAME=os.getenv('SMTP_USER'),MAIL_PASSWORD=os.getenv('SMTP_PASS'),MAIL_USE_TLS=True,MAIL_USE_SSL=False)
    Talisman(app,content_security_policy={'default-src':"'none'",'base-uri':"'none'",'frame-ancestors':"'none'"},force_https=os.getenv('FORCE_HTTPS','0')=='1',referrer_policy='no-referrer');db.init_app(app)
    configured_origins=os.getenv('CORS_ORIGINS');frontends=configured_origins or os.getenv('FRONTEND_URL','http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173');allowed_origins=[o.strip().rstrip('/') for o in frontends.split(',') if o.strip()];render_ui='https://public-online-service-provider-india.onrender.com'
    if render_ui not in allowed_origins:allowed_origins.append(render_ui)
    CORS(app,resources={r'/api/*':{'origins':allowed_origins}},supports_credentials=True,allow_headers=['Content-Type','Authorization','X-Razorpay-Signature'],methods=['GET','POST','PUT','PATCH','DELETE','OPTIONS']);Migrate(app,db)
    from .utils.limiter import limiter
    upload_limit_mb=int(os.getenv('MAX_UPLOAD_MB','10'));app.config['MAX_CONTENT_LENGTH']=(upload_limit_mb+1)*1024*1024
    limiter._default_limits=['2000 per day','500 per hour'];limiter.init_app(app)
    with app.app_context():
        if os.getenv('SKIP_DATABASE_BOOTSTRAP') != '1':
            db.create_all();ensure_user_schema(db);ensure_default_services();ensure_job_sources();ensure_admin_user()
    app.register_blueprint(auth.bp,url_prefix='/api/auth');app.register_blueprint(services.bp,url_prefix='/api/services');app.register_blueprint(orders.bp,url_prefix='/api/orders');app.register_blueprint(admin.bp,url_prefix='/api/admin');app.register_blueprint(reviews.bp,url_prefix='/api/reviews');app.register_blueprint(grievances.bp,url_prefix='/api/grievances');app.register_blueprint(categories.bp,url_prefix='/api/categories');app.register_blueprint(notifications.bp,url_prefix='/api/notifications');app.register_blueprint(messages.bp,url_prefix='/api/messages');app.register_blueprint(jobs.bp,url_prefix='/api/jobs');app.register_blueprint(scholarships.bp,url_prefix='/api/scholarships');app.register_blueprint(fees.bp,url_prefix='/api/fees');app.register_blueprint(payments.bp,url_prefix='/api/payments');app.register_blueprint(admin_payments.bp,url_prefix='/api/admin');app.register_blueprint(__import__('app.routes.uploads',fromlist=['bp']).bp,url_prefix='/api/uploads')
    @app.get('/')
    def index():return jsonify({'message':'Public Online Service Provider API'})
    @app.get('/health')
    def health():
        try:db.session.execute(text('SELECT 1'))
        except Exception:
            app.logger.exception('Database health check failed');return jsonify({'status':'unavailable'}),503
        return jsonify({'status':'ok'}),200
    return app