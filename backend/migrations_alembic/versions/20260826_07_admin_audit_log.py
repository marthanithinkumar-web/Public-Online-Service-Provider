"""add admin audit log

Revision ID: 20260826_07
Revises: 20260826_06
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = '20260826_07'
down_revision = '20260826_06'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if 'admin_audit_logs' in inspector.get_table_names():
        return
    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_admin_audit_logs_admin_id', 'admin_audit_logs', ['admin_id'])
    op.create_index('ix_admin_audit_logs_action', 'admin_audit_logs', ['action'])
    op.create_index('ix_admin_audit_logs_created_at', 'admin_audit_logs', ['created_at'])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if 'admin_audit_logs' not in inspector.get_table_names():
        return
    op.drop_index('ix_admin_audit_logs_created_at', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_action', table_name='admin_audit_logs')
    op.drop_index('ix_admin_audit_logs_admin_id', table_name='admin_audit_logs')
    op.drop_table('admin_audit_logs')
