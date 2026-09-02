"""add structured job fee rules

Revision ID: 20260902_16
Revises: 20260902_15
Create Date: 2026-09-02
"""

from alembic import op
import sqlalchemy as sa


revision = '20260902_16'
down_revision = '20260902_15'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {item['name'] for item in inspector.get_columns('job_notifications')}
    if 'fee_factors' not in columns:
        op.add_column('job_notifications', sa.Column('fee_factors', sa.JSON(), nullable=True))
    if 'fee_rules' not in columns:
        op.add_column('job_notifications', sa.Column('fee_rules', sa.JSON(), nullable=True))
    if 'fee_rules_verified_at' not in columns:
        op.add_column('job_notifications', sa.Column('fee_rules_verified_at', sa.DateTime(), nullable=True))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {item['name'] for item in inspector.get_columns('job_notifications')}
    for name in ('fee_rules_verified_at', 'fee_rules', 'fee_factors'):
        if name in columns:
            op.drop_column('job_notifications', name)
