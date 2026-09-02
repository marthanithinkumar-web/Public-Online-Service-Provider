"""add Razorpay payment records

Revision ID: 20260902_15
Revises: 20260831_14
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa


revision = '20260902_15'
down_revision = '20260831_14'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if 'payments' in set(inspector.get_table_names()):
        return
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False, server_default='razorpay'),
        sa.Column('purpose', sa.String(length=40), nullable=False, server_default='assistance_fee'),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='created'),
        sa.Column('razorpay_order_id', sa.String(length=100), nullable=False),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=True),
        sa.Column('failure_code', sa.String(length=120), nullable=True),
        sa.Column('failure_description', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('razorpay_order_id'),
        sa.UniqueConstraint('razorpay_payment_id'),
        sa.CheckConstraint('amount_paise >= 0', name='ck_payment_amount_nonnegative'),
    )
    op.create_index('ix_payments_order_id', 'payments', ['order_id'], unique=False)
    op.create_index('ix_payments_status', 'payments', ['status'], unique=False)
    op.create_index('ix_payments_razorpay_order_id', 'payments', ['razorpay_order_id'], unique=True)
    op.create_index('ix_payments_razorpay_payment_id', 'payments', ['razorpay_payment_id'], unique=True)


def downgrade():
    if 'payments' in set(sa.inspect(op.get_bind()).get_table_names()):
        op.drop_table('payments')
