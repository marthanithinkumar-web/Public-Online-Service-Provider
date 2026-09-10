"""manual refund records

Revision ID: 20260910_24
Revises: 20260906_23
"""
from alembic import op
import sqlalchemy as sa

revision = '20260910_24'
down_revision = '20260906_23'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'refunds',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('method', sa.String(length=30), nullable=False),
        sa.Column('reference', sa.String(length=160), nullable=False),
        sa.Column('refunded_at', sa.DateTime(), nullable=False),
        sa.Column('note', sa.String(length=2000), nullable=True),
        sa.Column('proof_filename', sa.String(length=255), nullable=True),
        sa.Column('proof_stored_path', sa.Text(), nullable=True),
        sa.Column('recorded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_refunds_order_id', 'refunds', ['order_id'])
    op.create_index('ix_refunds_reference', 'refunds', ['reference'])


def downgrade():
    op.drop_index('ix_refunds_reference', table_name='refunds')
    op.drop_index('ix_refunds_order_id', table_name='refunds')
    op.drop_table('refunds')
