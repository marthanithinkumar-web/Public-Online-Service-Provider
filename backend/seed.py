import os
from app.main import create_app
from app.utils.database import db
from app.models.service import Category, Service
from app.models.user import User
from app.utils.password import hash_password

app = create_app()

with app.app_context():
    # Create sample categories and services if missing
    if not Category.query.filter_by(name='Certificates').first():
        c1 = Category(name='Certificates')
        c2 = Category(name='Government Jobs')
        c3 = Category(name='MeeSeva / Public Services')
        db.session.add_all([c1,c2,c3])
        db.session.commit()
        s1 = Service(name='Residence Certificate', description='Assistance to apply for residence/domicile certificate', price_inr=30.0, keywords='residence,domicile,address,certificate', category_id=c1.id)
        s2 = Service(name='Ration Card Services', description='Help with Ration Card related applications', price_inr=50.0, keywords='ration,card,food,subsidy', category_id=c1.id)
        s3 = Service(name='Government Job Application', description='Assistance to apply for government job openings', price_inr=100.0, keywords='job,application,recruitment', category_id=c2.id)
        db.session.add_all([s1,s2,s3])
        db.session.commit()

    # Create admin user if ADMIN_EMAIL and ADMIN_PASSWORD provided
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    if admin_email and admin_pass:
        if not User.query.filter_by(email=admin_email).first():
            u = User(email=admin_email, password_hash=hash_password(admin_pass), is_admin=True)
            db.session.add(u)
            db.session.commit()
            print('Admin user created')
        else:
            print('Admin exists')
    else:
        print('ADMIN_EMAIL or ADMIN_PASSWORD not set; skipping admin creation')
