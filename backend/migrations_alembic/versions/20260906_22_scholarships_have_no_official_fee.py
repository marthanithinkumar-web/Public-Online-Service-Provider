"""Mark scholarship assistance services as having no official fee.

Revision ID: 20260906_22
Revises: 20260906_21
"""
from alembic import op

revision = '20260906_22'
down_revision = '20260906_21'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        UPDATE services
        SET official_fee_inr = 0,
            official_fee_status = 'none'
        WHERE lower(name) LIKE '%scholar%'
    """)


def downgrade():
    op.execute("""
        UPDATE services
        SET official_fee_inr = NULL,
            official_fee_status = 'unconfirmed'
        WHERE lower(name) LIKE '%scholar%'
    """)
