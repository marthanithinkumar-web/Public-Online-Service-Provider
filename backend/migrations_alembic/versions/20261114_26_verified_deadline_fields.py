"""Persist application cutoff times and source verification freshness.

Revision ID: 20261114_26
Revises: 20261104_25
Create Date: 2026-11-14
"""
from alembic import op
import sqlalchemy as sa

revision = "20261114_26"
down_revision = "20261104_25"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "job_notifications",
        sa.Column("deadline_cutoff_time", sa.Time(), nullable=True),
    )
    op.add_column(
        "job_notifications",
        sa.Column(
            "deadline_timezone",
            sa.String(length=64),
            nullable=False,
            server_default="Asia/Kolkata",
        ),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_successful_sync_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column(
            "consecutive_failures",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.execute(
        "UPDATE job_sources SET last_successful_sync_at = last_sync_completed_at "
        "WHERE last_sync_status = 'success' AND last_sync_completed_at IS NOT NULL"
    )
    # SQLite cannot DROP a column default with ALTER COLUMN. Keeping these
    # harmless defaults in SQLite preserves migration parity for the test suite;
    # PostgreSQL drops them because the application model owns the defaults.
    if op.get_bind().dialect.name != "sqlite":
        op.alter_column("job_notifications", "deadline_timezone", server_default=None)
        op.alter_column("job_sources", "consecutive_failures", server_default=None)


def downgrade():
    op.drop_column("job_sources", "consecutive_failures")
    op.drop_column("job_sources", "last_successful_sync_at")
    op.drop_column("job_notifications", "deadline_timezone")
    op.drop_column("job_notifications", "deadline_cutoff_time")
