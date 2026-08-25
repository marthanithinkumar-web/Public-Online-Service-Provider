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
    op.add_column('services', sa.Column('official_fee_inr', sa.Float(), nullable=True))
    op.add_column('services', sa.Column('official_fee_status', sa.String(length=20), nullable=False, server_default='unconfirmed'))
    op.add_column('orders', sa.Column('official_fee_inr', sa.Float(), nullable=True))
    op.add_column('orders', sa.Column('official_fee_status', sa.String(length=20), nullable=False, server_default='unconfirmed'))


def downgrade():
    op.drop_column('orders', 'official_fee_status')
    op.drop_column('orders', 'official_fee_inr')
    op.drop_column('services', 'official_fee_status')
    op.drop_column('services', 'official_fee_inr')
