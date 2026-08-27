"""add private client and admin support messages

Revision ID: 20260826_10
Revises: 20260826_09
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = '20260826_10'
down_revision = '20260826_09'
branch_labels = None
depends_on = None


def upgrade():
    if 'support_messages' in sa.inspect(op.get_bind()).get_table_names():
        return
    op.create_table(
        'support_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sender_user_id', sa.Integer(), nullable=False),
        sa.Column('sender_role', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read_by_client', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('read_by_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sender_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_support_messages_user_id', 'support_messages', ['user_id'])
    op.create_index('ix_support_messages_created_at', 'support_messages', ['created_at'])
    op.create_index('ix_support_messages_user_created', 'support_messages', ['user_id', 'created_at'])


def downgrade():
    if 'support_messages' not in sa.inspect(op.get_bind()).get_table_names():
        return
    op.drop_index('ix_support_messages_user_created', table_name='support_messages')
    op.drop_index('ix_support_messages_created_at', table_name='support_messages')
    op.drop_index('ix_support_messages_user_id', table_name='support_messages')
    op.drop_table('support_messages')
