import os
from app.main import create_app
from app.utils.database import db
from app.models.service import Category, Service
from app.models.service import PlatformSetting
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
        ('Aadhaar PVC Card Order', 'Help with ordering an Aadhaar PVC card through the official UIDAI process. Clients complete OTP and payment directly with UIDAI.', 'aadhaar pvc, aadhar pvc, uidai, pvc card, aadhaar card order'),
        ('DigiLocker Document Access Assistance', 'Guidance for finding and accessing eligible issued documents through DigiLocker. Clients sign in and complete OTP themselves.', 'digilocker, digital locker, issued documents, digital certificate, document access'),
        ('Official Document PDF Access Assistance', 'Help clients access an available official PDF or digital copy through the relevant official portal. This service does not create, alter or replace an identity document; clients complete any OTP or portal authentication themselves.', 'pdf, document pdf, digital copy, download, aadhaar, aadhar, e-aadhaar, voter id, e-epic, pan, e-pan, abha, apaar, digilocker, ration card, driving licence, rc, certificate, marksheet', 5.0),
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
        ('DOST Telangana Degree Admission Assistance', 'Assistance with eligible Telangana DOST undergraduate admission applications and option entry.', 'dost, dost telangana, degree admission, undergraduate, option entry'),
        ('Open School Admission / Examination Assistance', 'Assistance with eligible open-school admission, examination and status processes.', 'open school, nios, toss, admission, examination, distance education'),
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
        ('Non-Creamy Layer Certificate Assistance', 'Assistance with eligible non-creamy-layer certificate applications.', 'non creamy layer, ncl, obc certificate, bc certificate'),
        ('Police Clearance Certificate Assistance', 'Assistance with eligible police-clearance certificate application steps and appointments.', 'police clearance, pcc, clearance certificate, police verification'),
        ('Encumbrance Certificate Assistance', 'Assistance with eligible encumbrance-certificate searches and applications through the official process.', 'encumbrance certificate, ec, property document, registration'),
        ('Land Record / Pahani / Adangal Assistance', 'Assistance with eligible land-record, Pahani, Adangal or record-of-rights services.', 'land record, pahani, adangal, ror, dharani, meebhoomi'),
    ],
    'Government Jobs & Employment': [
        ('Government Job Application Assistance', 'Assistance with eligible government recruitment applications.', 'government job, govt job, recruitment, application, job'),
        ('State Government Job Application Assistance', 'Assistance with eligible state government recruitment applications.', 'state government job, recruitment, job application'),
        ('Police / Defence Recruitment Application Assistance', 'Assistance with eligible police and defence recruitment applications.', 'police, defence, army, navy, air force, recruitment'),
        ('Employment Registration Assistance', 'Assistance with eligible employment registration processes.', 'employment registration, job seeker, employment exchange'),
        ('Job Application Correction / Status Assistance', 'Assistance with eligible application corrections and status checks.', 'job correction, application correction, status, recruitment'),
        ('Apprenticeship Application Assistance', 'Assistance with eligible apprenticeship registration/application processes.', 'apprenticeship, apprentice, training, employment'),
        ('EPFO UAN Activation Assistance', 'Guidance for eligible EPFO UAN activation through the official process. Clients complete OTP themselves.', 'epfo, uan, uan activation, provident fund, pf'),
        ('EPF Claim / Transfer / Status Assistance', 'Guidance for eligible EPF claim, transfer and status processes. Clients authorize official steps themselves.', 'epf, pf claim, provident fund, pf transfer, claim status, epfo'),
        ('e-Shram Registration / Update Assistance', 'Assistance with eligible e-Shram registration and profile-update processes.', 'eshram, e shram, unorganised worker, labour card, worker registration'),
        ('National Career Service Registration Assistance', 'Assistance with eligible National Career Service job-seeker registration and profile setup.', 'ncs, national career service, job seeker, employment registration'),
        ('ESIC e-Pehchan / Benefit Assistance', 'Guidance for eligible ESIC e-Pehchan and benefit-related online processes.', 'esic, esi, e pehchan, employee insurance, benefit'),
    ],
    'Government Schemes & Welfare': [
        ('Government Scheme Application Assistance', 'Assistance with eligible central/state government scheme applications.', 'government scheme, scheme, welfare, application'),
        ('Pension Application Assistance', 'Assistance with eligible pension and social security applications.', 'pension, social security, welfare'),
        ('Farmer Scheme Application Assistance', 'Assistance with eligible farmer welfare scheme applications.', 'farmer, agriculture, farmer scheme, welfare'),
        ('Senior Citizen Service Assistance', 'Assistance with eligible senior citizen public-service applications.', 'senior citizen, welfare, public service'),
        ('Women & Child Welfare Scheme Assistance', 'Assistance with eligible women and child welfare schemes.', 'women welfare, child welfare, welfare scheme'),
        ('Disability Welfare Scheme Assistance', 'Assistance with eligible disability welfare schemes.', 'disability welfare, pwd, welfare scheme'),
        ('Housing Scheme Application Assistance', 'Assistance with eligible government housing-scheme applications.', 'housing scheme, house, welfare, government scheme'),
        ('PM-KISAN Registration / Status Assistance', 'Assistance with eligible PM-KISAN registration, correction and payment-status processes.', 'pm kisan, pmkisan, farmer, registration, beneficiary status'),
        ('Ayushman Bharat / PM-JAY Eligibility Assistance', 'Guidance for checking eligible Ayushman Bharat or PM-JAY beneficiary and card processes.', 'ayushman bharat, pmjay, pm jay, health card, eligibility'),
        ('ABHA Health ID Assistance', 'Guidance for eligible ABHA health-ID creation and profile processes. Clients complete OTP themselves.', 'abha, health id, ayushman bharat health account, digital health'),
        ('Ration Card - New / Member Update Assistance', 'Assistance with eligible ration-card applications, member additions and corrections.', 'ration card, food security card, member add, ration update, new ration'),
        ('Widow / Single Women Pension Assistance', 'Assistance with eligible widow or single-women pension application processes.', 'widow pension, single women pension, aasara, social security'),
        ('Labour Welfare Board Service Assistance', 'Assistance with eligible labour-welfare-board registration, renewal and benefit applications.', 'labour welfare, construction worker, labour card, worker benefit'),
    ],
    'Other Online Public Services': [
        ('MeeSeva / Public Service Application Assistance', 'Assistance with eligible MeeSeva and public-service applications.', 'meeseva, mee seva, public service, online service'),
        ('Government Application Status Assistance', 'Assistance with checking eligible government application status.', 'application status, status check, government'),
        ('Government Form Filling Assistance', 'Assistance with eligible online government form filling and document upload.', 'form filling, online form, government form, application'),
        ('Government Appointment Booking Assistance', 'Assistance with eligible online appointment booking.', 'appointment, booking, government appointment'),
        ('Online Document Upload Assistance', 'Assistance with preparing and uploading eligible documents to official portals.', 'document upload, online upload, application documents'),
        ('Government Portal Account Assistance', 'Assistance with eligible public-portal registration and account setup.', 'portal registration, government portal, account, registration'),
    ],
    'Business & Licence Assistance': [
        ('Udyam MSME Registration Assistance', 'Assistance with eligible Udyam/MSME registration through the official portal.', 'udyam, msme, micro enterprise, small business, business registration'),
        ('GST Registration Application Assistance', 'Form-filling guidance for eligible GST registration applications. Tax advice is not provided.', 'gst, gst registration, goods services tax, business tax registration'),
        ('FSSAI Registration / Licence Assistance', 'Assistance with eligible FSSAI food-business registration or licence applications.', 'fssai, food licence, food license, food business, registration'),
        ('Shop & Establishment Registration Assistance', 'Assistance with eligible shop-and-establishment registration or renewal processes.', 'shop establishment, trade registration, labour department, business licence'),
        ('Municipal Trade Licence Assistance', 'Assistance with eligible municipal trade-licence application and renewal processes.', 'trade licence, trade license, municipal, business licence, renewal'),
    ],
    'Utility & Civic Services': [
        ('Electricity New Connection / Name Change Assistance', 'Assistance with eligible electricity-connection applications and account-name changes.', 'electricity connection, power connection, name change, electricity service'),
        ('Electricity Bill Payment Assistance', 'Guidance for paying electricity bills through the official provider. Clients complete payment authorization themselves.', 'electricity bill, power bill, bill payment, utility'),
        ('Water Connection / Bill Assistance', 'Assistance with eligible water-connection, account and bill-payment processes.', 'water connection, water bill, utility, municipal water'),
        ('Property Tax Payment / Assessment Assistance', 'Guidance for eligible property-tax search, assessment and payment processes.', 'property tax, house tax, municipal tax, assessment'),
        ('LPG Connection / Subsidy Status Assistance', 'Guidance for eligible LPG connection and subsidy-status processes.', 'lpg, gas connection, cylinder, subsidy, dbtl'),
    ],
    'Travel & Ticketing Assistance': [
        ('Railway Ticket Booking Assistance', 'Guidance for railway ticket search and booking through the official railway process. Clients complete OTP and payment directly on the official portal.', 'railway, train, ticket, tickets, booking, irctc, travel'),
        ('Government Bus Ticket Booking Assistance', 'Guidance for bus search and booking through the relevant official transport portal. Clients complete OTP and payment themselves.', 'bus ticket, government bus, tsrtc, apsrtc, ticket booking, travel'),
        ('Student Bus Pass Assistance', 'Help with a student bus-pass application or renewal.', 'bus pass, student bus pass, concession pass, tgsrtc, tsrtc, apsrtc, renewal'),
        ('General Bus Pass Assistance', 'Help with a general commuter bus-pass application or renewal.', 'bus pass, general bus pass, commuter pass, tgsrtc, tsrtc, apsrtc, renewal'),
    ],
}

app = create_app()

with app.app_context():
    fee_setting = db.session.get(PlatformSetting, 'assistance_fee_inr')
    if fee_setting:
        try:
            catalog_fee = max(0.0, float(fee_setting.value))
        except (TypeError, ValueError):
            catalog_fee = 30.0
    else:
        existing_fee = db.session.query(Service.price_inr).filter(Service.price_inr.isnot(None)).order_by(Service.id.asc()).first()
        catalog_fee = float(existing_fee[0]) if existing_fee else 30.0
        db.session.add(PlatformSetting(key='assistance_fee_inr', value=f'{catalog_fee:.2f}'))
    for category_name, services in SERVICE_CATALOG.items():
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()
        for service_definition in services:
            name, description, keywords = service_definition[:3]
            initial_fee = service_definition[3] if len(service_definition) > 3 else catalog_fee
            service = Service.query.filter_by(name=name).first()
            # Preserve the existing record, fee, request relationships and ID
            # when improving a public-facing service label.
            if not service and name == 'Aadhaar PVC Card Order':
                service = Service.query.filter_by(name='Aadhaar PVC Card Order Guidance').first()
                if service:
                    service.name = name
            if not service:
                service = Service(name=name, description=description, price_inr=initial_fee, keywords=keywords, category_id=category.id, is_active=True)
                db.session.add(service)
            else:
                service.description = description
                service.keywords = keywords
                service.category_id = category.id
                if service.is_active is None:
                    service.is_active = True
    # Keep user-confirmed official charges clear and separate from assistance fees.
    official_fees = {
        'Income Certificate Assistance': 80.0,
        'Caste / Community Certificate Assistance': 80.0,
        'Residence / Domicile Certificate Assistance': 80.0,
        'PAN Card - New Application': 107.0,
        'PAN Card - Correction / Update': 107.0,
        'PAN Card - Reprint': 107.0,
    }
    for service_name, official_fee in official_fees.items():
        service = Service.query.filter_by(name=service_name).first()
        if service:
            service.official_fee_status = 'known'
            service.official_fee_inr = official_fee

    # Replace the older combined bus-pass listing without creating a duplicate.
    old_bus_pass = Service.query.filter_by(name='Student / Concession Bus Pass Assistance').first()
    new_student_pass = Service.query.filter_by(name='Student Bus Pass Assistance').first()
    if old_bus_pass and new_student_pass and old_bus_pass.id != new_student_pass.id:
        old_bus_pass.is_active = False
    db.session.commit()

    admin_email = os.getenv('ADMIN_EMAIL')
    admin_pass = os.getenv('ADMIN_PASSWORD')
    if admin_email and admin_pass:
        if not User.query.filter_by(email=admin_email).first():
            db.session.add(User(email=admin_email, password_hash=hash_password(admin_pass), is_admin=True))
            db.session.commit()
    print(f'Public service catalog ready: {Service.query.filter_by(is_active=True).count()} active services')
