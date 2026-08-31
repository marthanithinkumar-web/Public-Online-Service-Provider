"""add admin-only order archive state

Revision ID: 20260831_13
Revises: 20260830_12
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = '20260831_13'
down_revision = '20260830_12'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column['name'] for column in inspector.get_columns('orders')}
    if 'admin_archived_at' not in columns:
        op.add_column('orders', sa.Column('admin_archived_at', sa.DateTime(), nullable=True))

    indexes = {index['name'] for index in sa.inspect(bind).get_indexes('orders')}
    if 'ix_orders_admin_archived_at' not in indexes:
        op.create_index('ix_orders_admin_archived_at', 'orders', ['admin_archived_at'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = {index['name'] for index in inspector.get_indexes('orders')}
    if 'ix_orders_admin_archived_at' in indexes:
        op.drop_index('ix_orders_admin_archived_at', table_name='orders')

    columns = {column['name'] for column in sa.inspect(bind).get_columns('orders')}
    if 'admin_archived_at' in columns:
        op.drop_column('orders', 'admin_archived_at')
