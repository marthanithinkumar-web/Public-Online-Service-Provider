"""seed Mobile Recharge service and recharge assistance fee

Revision ID: 20260904_17
Revises: 20260902_16
"""
from alembic import op
import sqlalchemy as sa

revision = '20260904_17'
down_revision = '20260902_16'
branch_labels = None
depends_on = None

CATEGORY = 'Recharge & Bill Payments'
SERVICE = 'Mobile Recharge'
KEYWORDS = 'mobile recharge,recharge,prepaid,airtel,jio,vi,vodafone idea,bsnl,telecom,phone recharge,recharge plan,bill payment,bills'
DESCRIPTION = 'Assistance with prepaid mobile recharge plan selection and request tracking for supported Indian operators. Operator plan amount is kept separate from the website assistance fee.'


def upgrade():
    bind = op.get_bind()
    category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()
    if category_id is None:
        bind.execute(sa.text('INSERT INTO categories (name) VALUES (:name)'), {'name': CATEGORY})
        category_id = bind.execute(sa.text('SELECT id FROM categories WHERE name = :name'), {'name': CATEGORY}).scalar()

    service_id = bind.execute(sa.text('SELECT id FROM services WHERE name = :name'), {'name': SERVICE}).scalar()
    if service_id is None:
        bind.execute(sa.text('''
            INSERT INTO services
                (name, description, price_inr, keywords, category_id, is_active, official_fee_inr, official_fee_status)
            VALUES
                (:name, :description, :price, :keywords, :category_id, :active, :official_fee, :official_status)
        '''), {
            'name': SERVICE,
            'description': DESCRIPTION,
            'price': 10.0,
            'keywords': KEYWORDS,
            'category_id': category_id,
            'active': True,
            'official_fee': 0.0,
            'official_status': 'none',
        })
    else:
        bind.execute(sa.text('''
            UPDATE services
            SET category_id = COALESCE(category_id, :category_id),
                official_fee_inr = :official_fee,
                official_fee_status = :official_status,
                keywords = CASE WHEN keywords IS NULL OR keywords = '' THEN :keywords ELSE keywords END
            WHERE id = :service_id
        '''), {
            'category_id': category_id,
            'official_fee': 0.0,
            'official_status': 'none',
            'keywords': KEYWORDS,
            'service_id': service_id,
        })

    existing_setting = bind.execute(sa.text('SELECT key FROM platform_settings WHERE key = :key'), {'key': 'recharge_bill_assistance_fee_inr'}).scalar()
    if existing_setting is None:
        bind.execute(sa.text('INSERT INTO platform_settings (key, value) VALUES (:key, :value)'), {'key': 'recharge_bill_assistance_fee_inr', 'value': '10.00'})


def downgrade():
    # Keep user/admin-created production catalog data intact on downgrade.
    pass
