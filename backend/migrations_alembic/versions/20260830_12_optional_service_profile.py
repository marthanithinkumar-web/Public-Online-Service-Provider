"""add optional client service profile

Revision ID: 20260830_12
Revises: 20260828_11
Create Date: 2026-08-30
"""

from alembic import op
import sqlalchemy as sa


revision = '20260830_12'
down_revision = '20260828_11'
branch_labels = None
depends_on = None


COLUMNS = [
    ('date_of_birth', sa.Date()),
    ('gender', sa.String(length=50)),
    ('guardian_name', sa.String(length=200)),
    ('preferred_language', sa.String(length=50)),
    ('occupation', sa.String(length=120)),
    ('education_qualification', sa.String(length=150)),
    ('address_line', sa.String(length=300)),
    ('city', sa.String(length=120)),
    ('district', sa.String(length=120)),
    ('state', sa.String(length=120)),
    ('postal_code', sa.String(length=10)),
    ('alternate_phone', sa.String(length=50)),
    ('alternate_email', sa.String(length=200)),
    ('accessibility_needs', sa.String(length=500)),
    ('service_notes', sa.String(length=1000)),
    ('profile_updated_at', sa.DateTime()),
]


def upgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    for name, column_type in COLUMNS:
        if name not in existing:
            op.add_column('users', sa.Column(name, column_type, nullable=True))


def downgrade():
    existing = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    for name, _ in reversed(COLUMNS):
        if name in existing:
            op.drop_column('users', name)
