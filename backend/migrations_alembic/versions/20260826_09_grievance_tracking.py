"""add private grievance ownership, responses and history

Revision ID: 20260826_09
Revises: 20260826_08
Create Date: 2026-08-26
"""

from alembic import op
import sqlalchemy as sa


revision = '20260826_09'
down_revision = '20260826_08'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column['name'] for column in inspector.get_columns('grievances')}
    with op.batch_alter_table('grievances') as batch:
        if 'user_id' not in columns:
            batch.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
            batch.create_foreign_key('fk_grievances_user_id_users', 'users', ['user_id'], ['id'])
        if 'admin_response' not in columns:
            batch.add_column(sa.Column('admin_response', sa.Text(), nullable=True))
        if 'updated_at' not in columns:
            batch.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
    bind.execute(sa.text('UPDATE grievances SET user_id = (SELECT user_id FROM orders WHERE orders.id = grievances.order_id) WHERE user_id IS NULL AND order_id IS NOT NULL'))
    bind.execute(sa.text('UPDATE grievances SET user_id = (SELECT id FROM users WHERE lower(users.email) = lower(grievances.email) LIMIT 1) WHERE user_id IS NULL AND email IS NOT NULL'))
    bind.execute(sa.text('UPDATE grievances SET updated_at = created_at WHERE updated_at IS NULL'))
    # Legacy general grievances with no resolvable owner remain admin-only. New records always require user_id.
    if 'ix_grievances_user_id' not in {index['name'] for index in sa.inspect(bind).get_indexes('grievances')}:
        op.create_index('ix_grievances_user_id', 'grievances', ['user_id'])
    if 'grievance_history' not in sa.inspect(bind).get_table_names():
        op.create_table(
            'grievance_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('grievance_id', sa.Integer(), nullable=False),
            sa.Column('previous_status', sa.String(length=50), nullable=True),
            sa.Column('new_status', sa.String(length=50), nullable=False),
            sa.Column('changed_by', sa.String(length=200), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['grievance_id'], ['grievances.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_grievance_history_grievance_id', 'grievance_history', ['grievance_id'])


def downgrade():
    bind = op.get_bind()
    if 'grievance_history' in sa.inspect(bind).get_table_names():
        op.drop_index('ix_grievance_history_grievance_id', table_name='grievance_history')
        op.drop_table('grievance_history')
    columns = {column['name'] for column in sa.inspect(bind).get_columns('grievances')}
    with op.batch_alter_table('grievances') as batch:
        if 'user_id' in columns:
            batch.drop_index('ix_grievances_user_id')
            batch.drop_constraint('fk_grievances_user_id_users', type_='foreignkey')
            batch.drop_column('user_id')
        if 'admin_response' in columns:
            batch.drop_column('admin_response')
        if 'updated_at' in columns:
            batch.drop_column('updated_at')
