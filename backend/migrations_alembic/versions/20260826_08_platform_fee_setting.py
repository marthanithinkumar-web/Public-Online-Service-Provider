"""persist the website-wide assistance fee

Revision ID: 20260826_08
Revises: 20260826_07
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = '20260826_08'
down_revision = '20260826_07'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'platform_settings' not in inspector.get_table_names():
        op.create_table(
            'platform_settings',
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.String(length=500), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('key'),
        )
    services = sa.table('services', sa.column('id', sa.Integer()), sa.column('price_inr', sa.Float()))
    settings = sa.table('platform_settings', sa.column('key', sa.String()), sa.column('value', sa.String()), sa.column('updated_at', sa.DateTime()))
    existing = bind.execute(sa.select(settings.c.key).where(settings.c.key == 'assistance_fee_inr')).first()
    if not existing:
        first_fee = bind.execute(sa.select(services.c.price_inr).where(services.c.price_inr.is_not(None)).order_by(services.c.id.asc()).limit(1)).scalar()
        bind.execute(settings.insert().values(key='assistance_fee_inr', value=f'{float(first_fee if first_fee is not None else 30):.2f}', updated_at=sa.func.now()))


def downgrade():
    if 'platform_settings' in sa.inspect(op.get_bind()).get_table_names():
        op.drop_table('platform_settings')
