"""add admin web push subscriptions

Revision ID: 20260906_20
Revises: 20260906_19
"""
from alembic import op
import sqlalchemy as sa

revision = '20260906_20'
down_revision = '20260906_19'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'push_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh', sa.Text(), nullable=False),
        sa.Column('auth', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('endpoint'),
    )
    op.create_index('ix_push_subscriptions_user_id', 'push_subscriptions', ['user_id'], unique=False)


def downgrade():
    op.drop_index('ix_push_subscriptions_user_id', table_name='push_subscriptions')
    op.drop_table('push_subscriptions')
