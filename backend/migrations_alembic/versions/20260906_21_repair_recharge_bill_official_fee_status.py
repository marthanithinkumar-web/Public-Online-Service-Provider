"""repair recharge and bill official fee status

Revision ID: 20260906_21
Revises: 20260906_19
"""
from alembic import op
import sqlalchemy as sa

revision = '20260906_21'
down_revision = '20260906_19'
branch_labels = None
depends_on = None

SERVICES = (
    'Mobile Recharge',
    'Mobile Postpaid Bill Payment Assistance',
    'DTH Recharge Assistance',
    'Broadband / Landline Bill Payment Assistance',
    'FASTag Recharge Assistance',
    'Piped Gas Bill Payment Assistance',
)


def upgrade():
    bind = op.get_bind()
    for name in SERVICES:
        bind.execute(
            sa.text(
                '''
                UPDATE services
                SET official_fee_inr = 0.0,
                    official_fee_status = 'none'
                WHERE name = :name
                '''
            ),
            {'name': name},
        )


def downgrade():
    # Preserve the repaired production catalogue on downgrade.
    pass
