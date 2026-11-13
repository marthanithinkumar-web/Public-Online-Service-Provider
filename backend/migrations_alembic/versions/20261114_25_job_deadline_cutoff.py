"""add application deadline cutoff time and timezone

Revision ID: 20261114_25
Revises: 20260910_24
"""
from alembic import op
import sqlalchemy as sa

revision = '20261114_25'
down_revision = '20260910_24'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'job_notifications',
        sa.Column('deadline_cutoff_time', sa.String(length=5), nullable=True),
    )
    op.add_column(
        'job_notifications',
        sa.Column(
            'deadline_timezone',
            sa.String(length=80),
            nullable=False,
            server_default='Asia/Kolkata',
        ),
    )


def downgrade():
    op.drop_column('job_notifications', 'deadline_timezone')
    op.drop_column('job_notifications', 'deadline_cutoff_time')
