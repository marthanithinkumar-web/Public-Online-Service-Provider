"""add client email verification state

Revision ID: 20260828_11
Revises: 20260826_10
Create Date: 2026-08-28
"""

from alembic import op
import sqlalchemy as sa


revision = '20260828_11'
down_revision = '20260826_10'
branch_labels = None
depends_on = None


def upgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    if 'email_verified' not in columns:
        # Existing accounts stay usable; the application explicitly marks new
        # production registrations unverified until their link is opened.
        op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('users')}
    if 'email_verified' in columns:
        op.drop_column('users', 'email_verified')
