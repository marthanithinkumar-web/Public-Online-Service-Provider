"""add transparent official and assistance fee breakdown

Revision ID: 20260825_04
Revises: 20260824_03
Create Date: 2026-08-25
"""

from alembic import op
import sqlalchemy as sa

revision = '20260825_04'
down_revision = '20260824_03'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    service_columns = {column['name'] for column in inspector.get_columns('services')}
    order_columns = {column['name'] for column in inspector.get_columns('orders')}
    if 'official_fee_inr' not in service_columns:
        op.add_column('services', sa.Column('official_fee_inr', sa.Float(), nullable=True))
    if 'official_fee_status' not in service_columns:
        op.add_column('services', sa.Column('official_fee_status', sa.String(length=20), nullable=False, server_default='unconfirmed'))
    if 'official_fee_inr' not in order_columns:
        op.add_column('orders', sa.Column('official_fee_inr', sa.Float(), nullable=True))
    if 'official_fee_status' not in order_columns:
        op.add_column('orders', sa.Column('official_fee_status', sa.String(length=20), nullable=False, server_default='unconfirmed'))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    order_columns = {column['name'] for column in inspector.get_columns('orders')}
    service_columns = {column['name'] for column in inspector.get_columns('services')}
    if 'official_fee_status' in order_columns:
        op.drop_column('orders', 'official_fee_status')
    if 'official_fee_inr' in order_columns:
        op.drop_column('orders', 'official_fee_inr')
    if 'official_fee_status' in service_columns:
        op.drop_column('services', 'official_fee_status')
    if 'official_fee_inr' in service_columns:
        op.drop_column('services', 'official_fee_inr')
