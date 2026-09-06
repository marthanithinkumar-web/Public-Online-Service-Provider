"""refresh verified government service catalogue

Revision ID: 20260906_19
Revises: 20260906_20
"""
from alembic import op
import sqlalchemy as sa

revision = '20260906_19'
down_revision = '20260906_20'
branch_labels = None
depends_on = None

CATEGORY = 'Identity & Citizen Documents'

SERVICES = (
    (
        'Aadhaar - Mobile Number Update Assistance',
        'Guidance for the UIDAI Aadhaar app mobile-number update service. UIDAI currently supports mobile-number update through the Aadhaar app for eligible residents. If the old registered number is unavailable or no mobile number was previously registered, an Aadhaar Seva Kendra or authorised centre may still be required. Clients complete face authentication, OTP or other UIDAI authentication themselves.',
        'aadhaar mobile number update,aadhar phone number update,aadhaar phone link,uidai aadhaar app,mobile linking,aadhaar mobile change,phone number aadhaar',
        10.0, None, 'unconfirmed',
    ),
    (
        'Aadhaar - Address Update Assistance',
        'Guidance for eligible Aadhaar address updates through the UIDAI Aadhaar app or myAadhaar. The resident completes UIDAI authentication and submits the supporting address information directly on the official service.',
        'aadhaar address update,aadhar address change,uidai address update,myaadhaar address,aadhaar app address update,online aadhaar address',
        10.0, None, 'unconfirmed',
    ),
    (
        'Aadhaar - Email Update Assistance',
        'Guidance for Aadhaar email-address update through the UIDAI Aadhaar mobile application where available. UIDAI has announced a temporary waiver of the email-update service charge from 1 July 2026 through 31 December 2026. Clients complete UIDAI authentication themselves.',
        'aadhaar email update,aadhar email link,uidai email update,aadhaar app email,link email aadhaar,change email aadhaar',
        10.0, 0.0, 'none',
    ),
    (
        'Aadhaar - Document Update Assistance',
        'Guidance for the UIDAI Document Update service through myAadhaar for eligible residents. UIDAI has extended the online fee relaxation for Document Update through 14 June 2027. Clients upload documents and complete Aadhaar authentication only on the official UIDAI service.',
        'aadhaar document update,aadhar document update,myaadhaar document update,uidai documents,proof of identity,proof of address,online aadhaar document',
        10.0, 0.0, 'none',
    ),
    (
        'Aadhaar - Download e-Aadhaar Assistance',
        'Guidance for downloading e-Aadhaar through official UIDAI services. e-Aadhaar is an official electronic form of Aadhaar. The client completes UIDAI authentication and receives the document directly from UIDAI.',
        'download aadhaar,e aadhaar,e-aadhaar,aadhaar pdf,uidai download,aadhar download,digital aadhaar',
        5.0, 0.0, 'none',
    ),
    (
        'Aadhaar - Update / Request Status Assistance',
        'Guidance for checking Aadhaar update or request status through UIDAI online services, including requests submitted through the Aadhaar app or myAadhaar.',
        'aadhaar update status,aadhar status,track aadhaar request,uidai status,aadhaar request tracking',
        5.0, 0.0, 'none',
    ),
    (
        'Aadhaar - Biometric Lock / Unlock Assistance',
        'Guidance for UIDAI biometric lock and unlock controls available through the Aadhaar app. The client performs Aadhaar authentication and security actions directly in the official app.',
        'aadhaar biometric lock,biometric unlock,aadhaar security,uidai biometric,aadhaar app lock biometrics',
        5.0, 0.0, 'none',
    ),
    (
        'Aadhaar - Generate / Retrieve VID Assistance',
        'Guidance for generating or retrieving a Virtual ID (VID) through official UIDAI services. Clients complete Aadhaar authentication directly with UIDAI.',
        'aadhaar vid,virtual id,generate vid,retrieve vid,uidai virtual id,aadhar vid',
        5.0, 0.0, 'none',
    ),
    (
        'PAN - Aadhaar Linking Assistance',
        'Guidance for linking an existing PAN with Aadhaar through the Income Tax e-Filing portal. The service is available online for eligible taxpayers; exemptions and any applicable late-linking fee depend on the taxpayer case. Clients complete OTP, tax payment and final authorization directly on the Income Tax portal.',
        'pan aadhaar link,link pan aadhaar,aadhaar pan linking,income tax efiling,pan link status,pan aadhar,link aadhaar pan',
        10.0, None, 'unconfirmed',
    ),
)

GENERIC_AADHAAR = {
    'description': 'General Aadhaar update guidance covering UIDAI online/app services and centre-required updates. Mobile number and address updates are supported through the Aadhaar app for eligible residents; UIDAI also supports online Document Update, e-Aadhaar download, status tracking and other digital services. Name, date-of-birth, gender, biometric and other cases may still require an Aadhaar centre depending on current UIDAI rules.',
    'keywords': 'aadhaar,aadhar,uidai,aadhaar update,aadhar update,mobile number update,address update,email update,document update,e-aadhaar,status,biometric,vid,aadhaar app,myaadhaar',
}


def _category_id(bind):
    category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()
    if category_id is None:
        bind.execute(sa.text('INSERT INTO categories (name) VALUES (:name)'), {'name': CATEGORY})
        category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()
    return category_id


def upgrade():
    bind = op.get_bind()
    category_id = _category_id(bind)

    bind.execute(sa.text('''
        UPDATE services
        SET description = :description, keywords = :keywords, is_active = TRUE
        WHERE name = 'Aadhaar - Update Assistance'
    '''), GENERIC_AADHAAR)

    bind.execute(sa.text('''
        UPDATE services
        SET description = :description,
            keywords = :keywords,
            official_fee_inr = :official_fee,
            official_fee_status = :official_status,
            is_active = TRUE
        WHERE name = 'Aadhaar PVC Card Order'
    '''), {
        'description': 'Help with ordering an Aadhaar PVC card through the official UIDAI online service. UIDAI charges ₹75 inclusive of GST and Speed Post charges from 1 January 2026. Clients complete UIDAI authentication and payment directly with UIDAI.',
        'keywords': 'aadhaar pvc,aadhar pvc,uidai,pvc card,aadhaar card order,online aadhaar pvc,reprint aadhaar',
        'official_fee': 75.0,
        'official_status': 'known',
    })

    bind.execute(sa.text('''
        UPDATE services
        SET description = CASE
                WHEN name = 'Passport - New Application' THEN 'Assistance with passport application preparation and the current Passport Seva process. Passport Seva revised passport application fees with effect from 1 July 2026; the current official fee must be confirmed for the applicant and service type before payment.'
                ELSE 'Assistance with eligible passport renewal or reissue through Passport Seva. Passport application fees were revised with effect from 1 July 2026; the current official fee must be confirmed for the applicant and service type before payment.'
            END,
            official_fee_inr = NULL,
            official_fee_status = 'unconfirmed',
            is_active = TRUE
        WHERE name IN ('Passport - New Application', 'Passport - Renewal / Reissue')
    '''))

    for name, description, keywords, price, official_fee, official_status in SERVICES:
        service_id = bind.execute(sa.text('SELECT id FROM services WHERE name = :name'), {'name': name}).scalar()
        values = {
            'name': name,
            'description': description,
            'price': price,
            'keywords': keywords,
            'category_id': category_id,
            'active': True,
            'official_fee': official_fee,
            'official_status': official_status,
        }
        if service_id is None:
            bind.execute(sa.text('''
                INSERT INTO services
                    (name, description, price_inr, keywords, category_id, is_active, official_fee_inr, official_fee_status)
                VALUES
                    (:name, :description, :price, :keywords, :category_id, :active, :official_fee, :official_status)
            '''), values)
        else:
            values['service_id'] = service_id
            bind.execute(sa.text('''
                UPDATE services
                SET description = :description,
                    price_inr = :price,
                    keywords = :keywords,
                    category_id = :category_id,
                    is_active = :active,
                    official_fee_inr = :official_fee,
                    official_fee_status = :official_status
                WHERE id = :service_id
            '''), values)


def downgrade():
    # Keep production catalogue data intact on downgrade; service metadata is
    # intentionally additive and may already have client requests referencing it.
    pass
