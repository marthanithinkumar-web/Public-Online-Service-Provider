"""add verified job notification feed

Revision ID: 20260831_14
Revises: 20260831_13
Create Date: 2026-08-31
"""

from alembic import op
import sqlalchemy as sa


revision = '20260831_14'
down_revision = '20260831_13'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if 'job_sources' not in tables:
        op.create_table(
            'job_sources',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(length=60), nullable=False),
            sa.Column('name', sa.String(length=160), nullable=False),
            sa.Column('listing_url', sa.String(length=1000), nullable=False),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('last_sync_started_at', sa.DateTime(), nullable=True),
            sa.Column('last_sync_completed_at', sa.DateTime(), nullable=True),
            sa.Column('last_sync_status', sa.String(length=30), nullable=False, server_default='not_run'),
            sa.Column('last_error', sa.String(length=1000), nullable=True),
            sa.Column('fetched_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('published_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('key'),
        )
        op.create_index('ix_job_sources_key', 'job_sources', ['key'], unique=True)

    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if 'job_notifications' not in tables:
        op.create_table(
            'job_notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('source_id', sa.Integer(), nullable=False),
            sa.Column('slug', sa.String(length=320), nullable=False),
            sa.Column('external_id', sa.String(length=300), nullable=True),
            sa.Column('content_hash', sa.String(length=64), nullable=False),
            sa.Column('title', sa.String(length=500), nullable=False),
            sa.Column('organization', sa.String(length=500), nullable=False),
            sa.Column('job_type', sa.String(length=30), nullable=False, server_default='government'),
            sa.Column('appointment_type', sa.String(length=120), nullable=True),
            sa.Column('location', sa.String(length=300), nullable=True),
            sa.Column('qualification', sa.String(length=600), nullable=True),
            sa.Column('age_limit', sa.String(length=300), nullable=True),
            sa.Column('application_fee', sa.String(length=300), nullable=True),
            sa.Column('vacancies', sa.String(length=200), nullable=True),
            sa.Column('salary', sa.String(length=300), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('issue_date', sa.Date(), nullable=True),
            sa.Column('application_start_date', sa.Date(), nullable=True),
            sa.Column('deadline', sa.Date(), nullable=True),
            sa.Column('official_notice_url', sa.String(length=1200), nullable=False),
            sa.Column('application_url', sa.String(length=1200), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=False, server_default='needs_review'),
            sa.Column('verification_status', sa.String(length=60), nullable=False, server_default='official_source_checked'),
            sa.Column('confidence', sa.Float(), nullable=False, server_default='0'),
            sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('first_seen_at', sa.DateTime(), nullable=False),
            sa.Column('last_seen_at', sa.DateTime(), nullable=False),
            sa.Column('published_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_job_confidence'),
            sa.CheckConstraint("status IN ('published','needs_review','expired','hidden')", name='ck_job_status'),
            sa.ForeignKeyConstraint(['source_id'], ['job_sources.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('content_hash'),
            sa.UniqueConstraint('slug'),
            sa.UniqueConstraint('source_id', 'external_id', name='uq_job_source_external_id'),
        )
        for name, columns, unique in (
            ('ix_job_notifications_source_id', ['source_id'], False),
            ('ix_job_notifications_slug', ['slug'], True),
            ('ix_job_notifications_content_hash', ['content_hash'], True),
            ('ix_job_notifications_job_type', ['job_type'], False),
            ('ix_job_notifications_deadline', ['deadline'], False),
            ('ix_job_notifications_status', ['status'], False),
            ('ix_job_notifications_is_featured', ['is_featured'], False),
        ):
            op.create_index(name, 'job_notifications', columns, unique=unique)


def downgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if 'job_notifications' in tables:
        op.drop_table('job_notifications')
    if 'job_sources' in tables:
        op.drop_table('job_sources')
