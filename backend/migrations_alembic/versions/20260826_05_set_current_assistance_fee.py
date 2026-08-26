"""set the current assistance fee to thirty rupees

Revision ID: 20260826_05
Revises: 20260825_04
Create Date: 2026-08-26

This is intentionally a one-time data update. Administrators can change each
service price after deployment and normal application startup will not reset it.
Existing orders retain the fee snapshot agreed to when they were submitted.
"""

from alembic import op


revision = '20260826_05'
down_revision = '20260825_04'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('UPDATE services SET price_inr = 30.0')


def downgrade():
    # Previous per-service values cannot be reconstructed safely. A downgrade
    # therefore leaves the current administrator-configurable values intact.
    pass
