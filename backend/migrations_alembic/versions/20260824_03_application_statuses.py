"""normalize initial application status

Revision ID: 20260824_03
Revises: 20260824_02
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa

revision = '20260824_03'
down_revision = '20260824_02'
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("UPDATE orders SET status = 'Submitted' WHERE status = 'New'"))
    op.execute(sa.text("UPDATE order_status_history SET new_status = 'Submitted' WHERE new_status = 'New' AND previous_status IS NULL"))


def downgrade():
    op.execute(sa.text("UPDATE orders SET status = 'New' WHERE status = 'Submitted'"))
    op.execute(sa.text("UPDATE order_status_history SET new_status = 'New' WHERE new_status = 'Submitted' AND previous_status IS NULL"))
