"""WhatsApp message tracking.

Revision ID: 20261104_25
Revises: 20260910_24
"""

from alembic import op
import sqlalchemy as sa

revision = '20261104_25'
down_revision = '20260910_24'
branch_labels = None
depends_on = None


def _index_names(inspector, table):
    return {item['name'] for item in inspector.get_indexes(table)}


def _unique_names(inspector, table):
    return {item['name'] for item in inspector.get_unique_constraints(table)}


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'whatsapp_messages' not in set(inspector.get_table_names()):
        op.create_table(
            'whatsapp_messages',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('direction', sa.String(length=20), nullable=False),
            sa.Column('wa_message_id', sa.String(length=200), nullable=True),
            sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('from_number', sa.String(length=50), nullable=True),
            sa.Column('to_number', sa.String(length=50), nullable=True),
            sa.Column('message_type', sa.String(length=50), nullable=True),
            sa.Column('template_name', sa.String(length=200), nullable=True),
            sa.Column('body', sa.Text(), nullable=True),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
            sa.Column('event_key', sa.String(length=300), nullable=True),
            sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('last_error', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('event_key', name='uq_whatsapp_message_event_key'),
            sa.UniqueConstraint('wa_message_id', name='uq_whatsapp_message_wa_id'),
        )
        op.create_index('ix_whatsapp_messages_direction', 'whatsapp_messages', ['direction'])
        op.create_index('ix_whatsapp_messages_status', 'whatsapp_messages', ['status'])
        op.create_index('ix_whatsapp_messages_order_id', 'whatsapp_messages', ['order_id'])
        op.create_index('ix_whatsapp_messages_user_id', 'whatsapp_messages', ['user_id'])
        op.create_index('ix_whatsapp_messages_created_at', 'whatsapp_messages', ['created_at'])
        return

    # Repair partial installations additively. Adding the unique index is
    # intentionally allowed to fail if duplicate non-null Meta IDs require
    # operator cleanup first; silently skipping it would make idempotency unsafe.
    columns = {column['name'] for column in inspector.get_columns('whatsapp_messages')}
    required = {
        'direction': sa.String(length=20), 'wa_message_id': sa.String(length=200),
        'order_id': sa.Integer(), 'user_id': sa.Integer(),
        'from_number': sa.String(length=50), 'to_number': sa.String(length=50),
        'message_type': sa.String(length=50), 'template_name': sa.String(length=200),
        'body': sa.Text(), 'status': sa.String(length=50),
        'event_key': sa.String(length=300), 'retry_count': sa.Integer(),
        'last_error': sa.String(length=500), 'created_at': sa.DateTime(),
        'updated_at': sa.DateTime(),
    }
    columns_to_make_nonnull = []
    for name, column_type in required.items():
        if name not in columns:
            if name == 'direction':
                raise RuntimeError(
                    'whatsapp_messages exists without direction; inspect and repair it manually before retrying migration'
                )
            # Existing rows must be backfilled before a non-null constraint is
            # applied. This is deliberately two-phase so PostgreSQL does not
            # reject ALTER TABLE on a populated partial installation.
            op.add_column('whatsapp_messages', sa.Column(name, column_type, nullable=True))
            if name == 'status':
                op.execute(sa.text("UPDATE whatsapp_messages SET status = 'queued' WHERE status IS NULL"))
            elif name == 'retry_count':
                op.execute(sa.text('UPDATE whatsapp_messages SET retry_count = 0 WHERE retry_count IS NULL'))
            elif name in {'created_at', 'updated_at'}:
                op.execute(sa.text(
                    f'UPDATE whatsapp_messages SET {name} = CURRENT_TIMESTAMP WHERE {name} IS NULL'
                ))
            if name in {'status', 'retry_count', 'created_at', 'updated_at'}:
                columns_to_make_nonnull.append((name, column_type))

    # Existing partial schemas can have the right columns with weaker
    # nullability than the model. Repair those definitions too, but never
    # invent a direction for an existing row whose value is missing.
    inspector = sa.inspect(bind)
    existing_columns = {column['name']: column for column in inspector.get_columns('whatsapp_messages')}
    for name in ('direction', 'status', 'retry_count', 'created_at', 'updated_at'):
        column = existing_columns.get(name)
        if not column or not column.get('nullable') or any(item[0] == name for item in columns_to_make_nonnull):
            continue
        null_count = bind.execute(sa.text(
            f'SELECT COUNT(*) FROM whatsapp_messages WHERE {name} IS NULL'
        )).scalar_one()
        if null_count:
            if name == 'direction':
                raise RuntimeError(
                    'whatsapp_messages.direction contains NULL values; repair them manually before retrying migration'
                )
            if name == 'status':
                op.execute(sa.text("UPDATE whatsapp_messages SET status = 'queued' WHERE status IS NULL"))
            elif name == 'retry_count':
                op.execute(sa.text('UPDATE whatsapp_messages SET retry_count = 0 WHERE retry_count IS NULL'))
            else:
                op.execute(sa.text(
                    f'UPDATE whatsapp_messages SET {name} = CURRENT_TIMESTAMP WHERE {name} IS NULL'
                ))
        columns_to_make_nonnull.append((name, required[name]))

    if columns_to_make_nonnull:
        # Batch mode is a no-op style ALTER on PostgreSQL and recreates the
        # table safely on SQLite, which has no native ALTER COLUMN support.
        with op.batch_alter_table('whatsapp_messages') as batch_op:
            for name, column_type in columns_to_make_nonnull:
                batch_op.alter_column(name, existing_type=column_type, nullable=False)

    inspector = sa.inspect(bind)
    indexes = _index_names(inspector, 'whatsapp_messages')
    uniques = _unique_names(inspector, 'whatsapp_messages')
    if 'uq_whatsapp_message_event_key' not in uniques and 'uq_whatsapp_message_event_key' not in indexes:
        op.create_index('uq_whatsapp_message_event_key', 'whatsapp_messages', ['event_key'], unique=True)
    if 'uq_whatsapp_message_wa_id' not in uniques and 'uq_whatsapp_message_wa_id' not in indexes:
        op.create_index('uq_whatsapp_message_wa_id', 'whatsapp_messages', ['wa_message_id'], unique=True)
    for name, column in (
        ('ix_whatsapp_messages_direction', 'direction'),
        ('ix_whatsapp_messages_status', 'status'),
        ('ix_whatsapp_messages_order_id', 'order_id'),
        ('ix_whatsapp_messages_user_id', 'user_id'),
        ('ix_whatsapp_messages_created_at', 'created_at'),
    ):
        if name not in indexes:
            op.create_index(name, 'whatsapp_messages', [column])


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'whatsapp_messages' not in set(inspector.get_table_names()):
        return
    indexes = _index_names(inspector, 'whatsapp_messages')
    for name in (
        'uq_whatsapp_message_wa_id', 'uq_whatsapp_message_event_key',
        'ix_whatsapp_messages_status', 'ix_whatsapp_messages_direction',
        'ix_whatsapp_messages_created_at', 'ix_whatsapp_messages_user_id',
        'ix_whatsapp_messages_order_id',
    ):
        if name in indexes:
            op.drop_index(name, table_name='whatsapp_messages')
    op.drop_table('whatsapp_messages')
