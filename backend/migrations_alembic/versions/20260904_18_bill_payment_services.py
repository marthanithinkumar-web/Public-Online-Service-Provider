"""seed additional recharge and bill payment assistance services

Revision ID: 20260904_18
Revises: 20260904_17
"""
from alembic import op
import sqlalchemy as sa

revision = '20260904_18'
down_revision = '20260904_17'
branch_labels = None
depends_on = None

CATEGORY = 'Recharge & Bill Payments'
SERVICES = (
    (
        'Mobile Postpaid Bill Payment Assistance',
        'Assistance with postpaid mobile bill details and request tracking for supported Indian operators. The bill amount is separate from the website assistance fee and payment authorization remains with the client.',
        'mobile postpaid,postpaid bill,mobile bill,airtel postpaid,jio postpaid,vi postpaid,bsnl postpaid,telecom bill,bill payment',
    ),
    (
        'DTH Recharge Assistance',
        'Assistance with DTH recharge details, plan selection and request tracking. The DTH recharge amount is separate from the website assistance fee and payment authorization remains with the client.',
        'dth recharge,tata play,airtel digital tv,dish tv,d2h,videocon d2h,sun direct,tv recharge,recharge',
    ),
    (
        'Broadband / Landline Bill Payment Assistance',
        'Assistance with broadband or landline bill details and request tracking. The provider bill amount is separate from the website assistance fee and payment authorization remains with the client.',
        'broadband bill,landline bill,internet bill,fiber bill,airtel xstream,jiofiber,bsnl broadband,act fibernet,bill payment',
    ),
    (
        'FASTag Recharge Assistance',
        'Assistance with FASTag recharge details and request tracking. The FASTag recharge amount is separate from the website assistance fee and payment authorization remains with the client.',
        'fastag recharge,fast tag,toll recharge,vehicle tag,nhaI,highway toll,recharge',
    ),
    (
        'Piped Gas Bill Payment Assistance',
        'Assistance with piped-gas bill details and request tracking. The gas bill amount is separate from the website assistance fee and payment authorization remains with the client.',
        'piped gas bill,gas bill,png bill,city gas,consumer number,bill payment,utility',
    ),
)


def upgrade():
    bind = op.get_bind()
    category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()
    if category_id is None:
        bind.execute(sa.text('INSERT INTO categories (name) VALUES (:name)'), {'name': CATEGORY})
        category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()

    for name, description, keywords in SERVICES:
        service_id = bind.execute(sa.text('SELECT id FROM services WHERE name = :name'), {'name': name}).scalar()
        values = {
            'name': name,
            'description': description,
            'price': 10.0,
            'keywords': keywords,
            'category_id': category_id,
            'active': True,
            'official_fee': 0.0,
            'official_status': 'none',
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
    # Keep production catalog data intact on downgrade.
    pass
