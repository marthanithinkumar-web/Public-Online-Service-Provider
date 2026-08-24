"""admin notifications and account security

Revision ID: 20260824_01
Revises:
Create Date: 2026-08-24
"""

from alembic import op
import sqlalchemy as sa

revision = '20260824_01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    user_columns = {column['name'] for column in inspector.get_columns('users')}
    if 'is_active' not in user_columns:
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    if 'token_version' not in user_columns:
        op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'))
    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
        op.create_index('ix_notifications_order_id', 'notifications', ['order_id'])
    if 'revoked_tokens' not in tables:
        op.create_table(
            'revoked_tokens', sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('jti', sa.String(length=64), nullable=False, unique=True),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_revoked_tokens_jti', 'revoked_tokens', ['jti'], unique=True)
    if 'admin_login_challenges' not in tables:
        op.create_table(
            'admin_login_challenges', sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('code_hash', sa.String(length=64), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_admin_login_challenges_user_id', 'admin_login_challenges', ['user_id'])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'notifications' in inspector.get_table_names():
        op.drop_index('ix_notifications_order_id', table_name='notifications')
        op.drop_index('ix_notifications_user_id', table_name='notifications')
        op.drop_table('notifications')
    tables = set(sa.inspect(bind).get_table_names())
    if 'admin_login_challenges' in tables:
        op.drop_index('ix_admin_login_challenges_user_id', table_name='admin_login_challenges')
        op.drop_table('admin_login_challenges')
    if 'revoked_tokens' in tables:
        op.drop_index('ix_revoked_tokens_jti', table_name='revoked_tokens')
        op.drop_table('revoked_tokens')
