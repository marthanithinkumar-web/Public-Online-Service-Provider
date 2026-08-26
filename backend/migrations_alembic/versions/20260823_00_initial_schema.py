"""create the original application schema

Revision ID: 20260823_00
Revises:
Create Date: 2026-08-23

This baseline makes the Alembic history capable of creating a brand-new
database.  The guards also keep it safe for older installations whose tables
were originally created by SQLAlchemy before migrations were introduced.
"""

from alembic import op
import sqlalchemy as sa


revision = '20260823_00'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    tables = set(sa.inspect(op.get_bind()).get_table_names())

    if 'categories' not in tables:
        op.create_table(
            'categories',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )
        tables.add('categories')

    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(length=200), nullable=False),
            sa.Column('password_hash', sa.String(length=500), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('token_version', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
        )
        tables.add('users')

    if 'services' not in tables:
        op.create_table(
            'services',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=300), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('price_inr', sa.Float(), nullable=True, server_default='0'),
            sa.Column('keywords', sa.String(length=500), nullable=True),
            sa.Column('category_id', sa.Integer(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('services')

    if 'orders' not in tables:
        op.create_table(
            'orders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_code', sa.String(length=50), nullable=False),
            sa.Column('client_name', sa.String(length=200), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=False),
            sa.Column('email', sa.String(length=200), nullable=True),
            sa.Column('contact_method', sa.String(length=50), nullable=True),
            sa.Column('service_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('fee_inr', sa.Float(), nullable=True, server_default='0'),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='Submitted'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['service_id'], ['services.id']),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('order_code'),
        )
        tables.add('orders')

    if 'order_status_history' not in tables:
        op.create_table(
            'order_status_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=False),
            sa.Column('previous_status', sa.String(length=50), nullable=True),
            sa.Column('new_status', sa.String(length=50), nullable=True),
            sa.Column('changed_by', sa.String(length=200), nullable=True),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('order_status_history')

    if 'attachments' not in tables:
        op.create_table(
            'attachments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('filename', sa.String(length=300), nullable=False),
            sa.Column('stored_path', sa.String(length=1000), nullable=False),
            sa.Column('uploaded_by', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
            sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
            sa.PrimaryKeyConstraint('id'),
        )
        tables.add('attachments')

    if 'grievances' not in tables:
        op.create_table(
            'grievances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('grievance_code', sa.String(length=50), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('client_name', sa.String(length=200), nullable=False),
            sa.Column('phone', sa.String(length=50), nullable=False),
            sa.Column('email', sa.String(length=200), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=True, server_default='New'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('grievance_code'),
        )
        tables.add('grievances')

    if 'reviews' not in tables:
        op.create_table(
            'reviews',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('order_id', sa.Integer(), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('client_name', sa.String(length=200), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=True, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    # Drop only baseline tables. Later migrations remove their own additions
    # before this downgrade is reached.
    inspector = sa.inspect(op.get_bind())
    for table in (
        'reviews',
        'grievances',
        'attachments',
        'order_status_history',
        'orders',
        'services',
        'users',
        'categories',
    ):
        if table in inspector.get_table_names():
            op.drop_table(table)
