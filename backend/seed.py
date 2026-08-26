import os
from app.main import create_app
from app.utils.database import db
from app.models.service import Category, Service
from app.models.user import User
from app.utils.password import hash_password

SERVICE_CATALOG = {
    'Identity & Citizen Documents': [
        ('PAN Card - New Application', 'Assistance with a new PAN application.', 'pan, pan card, permanent account number, new pan, pancard'),
        ('PAN Card - Correction / Update', 'Assistance with eligible PAN corrections and updates.', 'pan, pan card, pancard, pan correction, pan update, name correction, dob correction'),
        ('PAN Card - Reprint', 'Assistance with PAN reprint/reissue requests.', 'pan, pan card, reprint, reprint pan, pancard'),
        ('Voter ID - New Registration', 'Assistance with new voter registration through the official process.', 'voter, voter id, epic, election card, new voter, registration'),
        ('Voter ID - Correction / Update', 'Assistance with eligible voter detail corrections.', 'voter, voter id, epic, correction, update, name, dob, address'),
        ('Voter ID - Address / Constituency Change', 'Assistance with eligible voter address or constituency updates.', 'voter, voter id, epic, address change, constituency change, transfer'),
        ('Aadhaar - Update Assistance', 'Assistance for eligible Aadhaar demographic/document update processes; official rules apply.', 'aadhaar, aadhar, uidai, aadhaar update, aadhar update, demographic update'),
        ('Passport - New Application', 'Assistance with passport application preparation and official process.', 'passport, new passport, passport application, psk'),
        ('Passport - Renewal / Reissue', 'Assistance with eligible passport renewal/reissue applications.', 'passport, renewal, reissue, passport renewal'),
        ('Driving Licence / Learner Licence Assistance', 'Assistance with eligible learner and driving licence application processes.', 'driving licence, driving license, dl, learner licence, llr, rto'),
        ('RC / Vehicle Service Assistance', 'Assistance with eligible vehicle-registration related online services.', 'rc, vehicle registration, transport, rto, vehicle service'),
    ],
    'Scholarships & Student Welfare': [
        ('ePASS - Fresh Scholarship Application', 'Assistance with eligible ePASS fresh scholarship applications.', 'epass, e-pass, scholarship, fresh, post matric, pre matric, telangana'),
        ('ePASS - Scholarship Renewal', 'Assistance with eligible ePASS scholarship renewal applications.', 'epass, e-pass, renewal, scholarship renewal, post matric, telangana'),
        ('National Scholarship Portal (NSP) Assistance', 'Assistance with eligible NSP scholarship applications and renewals.', 'nsp, national scholarship portal, scholarship, fresh, renewal'),
        ('Pre-Matric Scholarship Assistance', 'Assistance with eligible pre-matric scholarship applications.', 'pre matric, scholarship, student, school'),
        ('Post-Matric Scholarship Assistance', 'Assistance with eligible post-matric scholarship applications.', 'post matric, scholarship, college, student'),
        ('BC Welfare Scholarship Assistance', 'Assistance with eligible BC welfare scholarship applications.', 'bc welfare, bc scholarship, backward classes, scholarship'),
        ('SC Welfare Scholarship Assistance', 'Assistance with eligible SC welfare scholarship applications.', 'sc welfare, sc scholarship, scheduled caste, scholarship'),
        ('ST Welfare Scholarship Assistance', 'Assistance with eligible ST welfare scholarship applications.', 'st welfare, st scholarship, scheduled tribe, scholarship'),
        ('Minority Scholarship Assistance', 'Assistance with eligible minority scholarship applications.', 'minority scholarship, scholarship, student'),
        ('EWS / Student Welfare Scholarship Assistance', 'Assistance with eligible EWS and student welfare scholarship processes.', 'ews, scholarship, student welfare, education'),
        ('Scholarship Application Status Assistance', 'Assistance with checking eligible scholarship application status.', 'scholarship status, epass status, nsp status, application status'),
    ],
    'Entrance & Competitive Exams': [
        ('POLYCET Application Assistance', 'Assistance with Polytechnic entrance application.', 'polycet, poly cet, polytechnic, diploma entrance, entrance exam'),
        ('TG EAPCET / TS EAMCET Application Assistance', 'Assistance with Telangana EAPCET application.', 'tg eapcet, ts eapcet, tseamcet, ts eamcet, eamcet, engineering, agriculture, pharmacy'),
        ('AP EAPCET / AP EAMCET Application Assistance', 'Assistance with Andhra Pradesh EAPCET application.', 'ap eapcet, ap eamcet, eamcet, engineering, agriculture, pharmacy'),
        ('ECET Application Assistance', 'Assistance with eligible engineering common entrance applications.', 'ecet, engineering common entrance, lateral entry'),
        ('ICET Application Assistance', 'Assistance with MBA/MCA entrance applications.', 'icet, mba, mca, entrance exam'),
        ('PGECET Application Assistance', 'Assistance with postgraduate engineering entrance applications.', 'pgecet, pg ecet, mtech, engineering entrance'),
        ('EdCET Application Assistance', 'Assistance with education entrance applications.', 'edcet, ed cet, bed, education entrance'),
        ('LAWCET Application Assistance', 'Assistance with law entrance applications.', 'lawcet, law cet, llb, llm, law entrance'),
        ('CPGET Application Assistance', 'Assistance with postgraduate entrance applications.', 'cpget, pg entrance, osmania, postgraduate'),
        ('NEET Application Assistance', 'Assistance with NEET application preparation and official process.', 'neet, medical entrance, ug medical'),
        ('JEE Main Application Assistance', 'Assistance with JEE Main application preparation.', 'jee, jee main, engineering entrance, nta'),
        ('CUET Application Assistance', 'Assistance with CUET application preparation.', 'cuet, common university entrance, nta, university admission'),
        ('UGC NET Application Assistance', 'Assistance with UGC NET application preparation.', 'ugc net, net, nta, assistant professor, jrf'),
        ('SSC Examination Application Assistance', 'Assistance with eligible SSC examination applications.', 'ssc, staff selection commission, cgl, chsl, mts, gd'),
        ('UPSC Examination Application Assistance', 'Assistance with eligible UPSC examination applications.', 'upsc, civil services, cds, nda, examination'),
        ('Railway Examination Application Assistance', 'Assistance with eligible railway recruitment applications.', 'railway, rrb, rrc, ntpc, group d, technician'),
        ('Banking Examination Application Assistance', 'Assistance with eligible banking recruitment applications.', 'bank, banking, ibps, sbi, clerk, po'),
        ('TET Examination Application Assistance', 'Assistance with eligible teacher eligibility test applications.', 'tet, tgt, teacher eligibility test, education, teacher'),
        ('SET Examination Application Assistance', 'Assistance with eligible state eligibility test applications.', 'set, state eligibility test, assistant professor'),
    ],
    'Gurukulam & Residential Schools': [
        ('BC Welfare Gurukulam Admission', 'Assistance with eligible BC welfare residential school admissions.', 'bc gurukulam, bc welfare, gurukulam, residential school, admission'),
        ('SC Welfare Gurukulam Admission', 'Assistance with eligible SC welfare residential school admissions.', 'sc gurukulam, sc welfare, gurukulam, residential school, admission'),
        ('ST Welfare Gurukulam Admission', 'Assistance with eligible ST welfare residential school admissions.', 'st gurukulam, st welfare, gurukulam, residential school, admission'),
        ('Minority Residential School Admission', 'Assistance with eligible minority residential school admissions.', 'minority school, residential school, admission'),
        ('Sainik School Application Assistance', 'Assistance with eligible Sainik School entrance applications.', 'sainik, sainik school, aissee, school admission'),
        ('Jawahar Navodaya Vidyalaya Application Assistance', 'Assistance with eligible JNV/Navodaya applications.', 'navodaya, jawahar navodaya, jnv, class 6, class 9, admission'),
        ('Residential School Application Status Assistance', 'Assistance with checking eligible residential-school application status.', 'gurukulam status, residential school status, admission status'),
    ],
    'Admissions': [
        ('IIIT Basara / RGUKT Admission Assistance', 'Assistance with eligible IIIT Basara/RGUKT admission applications.', 'iiit basara, rgukt, basara, iiit, btech admission, admission'),
        ('Polytechnic Admission Assistance', 'Assistance with eligible polytechnic counselling/admission processes.', 'polytechnic, diploma, admission, counselling'),
        ('ITI Admission Assistance', 'Assistance with eligible ITI admission processes.', 'iti, industrial training institute, admission'),
        ('Degree Admission Assistance', 'Assistance with eligible degree admission and counselling processes.', 'degree, ug, admission, counselling, college'),
        ('Engineering Admission Assistance', 'Assistance with eligible engineering admission/counselling processes.', 'engineering, btech, admission, counselling, eamcet'),
        ('Medical Admission Assistance', 'Assistance with eligible medical admission processes.', 'medical, mbbs, bds, admission, neet, counselling'),
        ('Skill Development Admission Assistance', 'Assistance with eligible government/approved skill-development applications.', 'skill development, training, vocational, admission'),
        ('University / College Admission Form Assistance', 'Assistance with eligible online university and college admission forms.', 'college admission, university admission, application form'),
    ],
    'Certificates & Public Documents': [
        ('Income Certificate Assistance', 'Assistance with eligible income certificate applications.', 'income certificate, income, certificate'),
        ('Caste / Community Certificate Assistance', 'Assistance with eligible caste/community certificate applications.', 'caste certificate, community certificate, bc, sc, st, certificate'),
        ('Residence / Domicile Certificate Assistance', 'Assistance with eligible residence/domicile certificate applications.', 'residence, domicile, nativity, address certificate'),
        ('EWS Certificate Assistance', 'Assistance with eligible EWS certificate applications.', 'ews, economically weaker section, certificate'),
        ('Birth Certificate Assistance', 'Assistance with eligible birth certificate services.', 'birth certificate, birth, certificate'),
        ('Death Certificate Assistance', 'Assistance with eligible death certificate services.', 'death certificate, death, certificate'),
        ('Marriage Certificate Assistance', 'Assistance with eligible marriage certificate services.', 'marriage certificate, marriage, certificate'),
        ('Family / Legal Heir Certificate Assistance', 'Assistance with eligible family/legal heir certificate processes.', 'family certificate, legal heir, heir certificate'),
        ('Disability Certificate Assistance', 'Assistance with eligible disability certificate processes.', 'disability certificate, pwd, udid, certificate'),
    ],
    'Government Jobs & Employment': [
        ('Government Job Application Assistance', 'Assistance with eligible government recruitment applications.', 'government job, govt job, recruitment, application, job'),
        ('State Government Job Application Assistance', 'Assistance with eligible state government recruitment applications.', 'state government job, recruitment, job application'),
        ('Police / Defence Recruitment Application Assistance', 'Assistance with eligible police and defence recruitment applications.', 'police, defence, army, navy, air force, recruitment'),
        ('Employment Registration Assistance', 'Assistance with eligible employment registration processes.', 'employment registration, job seeker, employment exchange'),
        ('Job Application Correction / Status Assistance', 'Assistance with eligible application corrections and status checks.', 'job correction, application correction, status, recruitment'),
        ('Apprenticeship Application Assistance', 'Assistance with eligible apprenticeship registration/application processes.', 'apprenticeship, apprentice, training, employment'),
    ],
    'Government Schemes & Welfare': [
        ('Government Scheme Application Assistance', 'Assistance with eligible central/state government scheme applications.', 'government scheme, scheme, welfare, application'),
        ('Pension Application Assistance', 'Assistance with eligible pension and social security applications.', 'pension, social security, welfare'),
        ('Farmer Scheme Application Assistance', 'Assistance with eligible farmer welfare scheme applications.', 'farmer, agriculture, farmer scheme, welfare'),
        ('Senior Citizen Service Assistance', 'Assistance with eligible senior citizen public-service applications.', 'senior citizen, welfare, public service'),
        ('Women & Child Welfare Scheme Assistance', 'Assistance with eligible women and child welfare schemes.', 'women welfare, child welfare, welfare scheme'),
        ('Disability Welfare Scheme Assistance', 'Assistance with eligible disability welfare schemes.', 'disability welfare, pwd, welfare scheme'),
        ('Housing Scheme Application Assistance', 'Assistance with eligible government housing-scheme applications.', 'housing scheme, house, welfare, government scheme'),
    ],
    'Other Online Public Services': [
        ('MeeSeva / Public Service Application Assistance', 'Assistance with eligible MeeSeva and public-service applications.', 'meeseva, mee seva, public service, online service'),
        ('Government Application Status Assistance', 'Assistance with checking eligible government application status.', 'application status, status check, government'),
        ('Government Form Filling Assistance', 'Assistance with eligible online government form filling and document upload.', 'form filling, online form, government form, application'),
        ('Government Appointment Booking Assistance', 'Assistance with eligible online appointment booking.', 'appointment, booking, government appointment'),
        ('Online Document Upload Assistance', 'Assistance with preparing and uploading eligible documents to official portals.', 'document upload, online upload, application documents'),
        ('Government Portal Account Assistance', 'Assistance with eligible public-portal registration and account setup.', 'portal registration, government portal, account, registration'),
    ],
    'Travel & Ticketing Assistance': [
        ('Railway Ticket Booking Assistance', 'Guidance for railway ticket search and booking through the official railway process. Clients complete OTP and payment directly on the official portal.', 'railway, train, ticket, tickets, booking, irctc, travel'),
    ],
}

app = create_app()

with app.app_context():
    for category_name, services in SERVICE_CATALOG.items():
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        for name, description, keywords in services:
            service = Service.query.filter_by(name=name).first()
            if not service:
                service = Service(name=name, description=description, price_inr=30.0, keywords=keywords, category_id=category.id, is_active=True)
                db.session.add(service)
            else:
                service.description = description
                service.keywords = keywords
                service.category_id = category.id
                if service.is_active is None:
                    service.is_active = True
    db.session.commit()

    admin_email = os.getenv('ADMIN_EMAIL')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    if admin_email and admin_pass:
        if not User.query.filter_by(email=admin_email).first():
            db.session.add(User(email=admin_email, password_hash=hash_password(admin_pass), is_admin=True))
            db.session.commit()
    print(f'Public service catalog ready: {Service.query.filter_by(is_active=True).count()} active services')
