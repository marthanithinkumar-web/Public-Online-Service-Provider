"""track application update times

Revision ID: 20260824_02
Revises: 20260824_01
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa

revision = '20260824_02'
down_revision = '20260824_01'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    columns = {column['name'] for column in inspector.get_columns('orders')}
    if 'updated_at' not in columns:
        op.add_column('orders', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.execute(sa.text('UPDATE orders SET updated_at = created_at WHERE updated_at IS NULL'))


def downgrade():
    columns = {column['name'] for column in sa.inspect(op.get_bind()).get_columns('orders')}
    if 'updated_at' in columns:
        op.drop_column('orders', 'updated_at')
