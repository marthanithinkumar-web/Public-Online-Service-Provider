"""add indexes for common client and admin queries

Revision ID: 20260826_06
Revises: 20260826_05
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = '20260826_06'
down_revision = '20260826_05'
branch_labels = None
depends_on = None


INDEXES = [
    ('ix_orders_user_created', 'orders', ['user_id', 'created_at']),
    ('ix_orders_status_created', 'orders', ['status', 'created_at']),
    ('ix_order_status_history_order_created', 'order_status_history', ['order_id', 'created_at']),
    ('ix_attachments_order_created', 'attachments', ['order_id', 'created_at']),
    ('ix_notifications_user_read_created', 'notifications', ['user_id', 'is_read', 'created_at']),
    ('ix_services_active_name', 'services', ['is_active', 'name']),
]


def upgrade():
    inspector=sa.inspect(op.get_bind())
    tables=set(inspector.get_table_names())
    for name,table,columns in INDEXES:
        if table not in tables:
            continue
        existing={index['name'] for index in inspector.get_indexes(table)}
        if name not in existing:
            op.create_index(name,table,columns)


def downgrade():
    inspector=sa.inspect(op.get_bind())
    tables=set(inspector.get_table_names())
    for name,table,_ in reversed(INDEXES):
        if table not in tables:
            continue
        existing={index['name'] for index in inspector.get_indexes(table)}
        if name in existing:
            op.drop_index(name,table_name=table)
