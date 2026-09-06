"""Prepare production data/schema safety work before Alembic runs.

The job-feed table preparation preserves compatibility with an older partial
migration. Historical client-document retention is also available as an
explicit one-shot maintenance action, disabled unless the Render environment
sets ``RUN_HISTORICAL_ATTACHMENT_PURGE=1``.
"""

import os

from sqlalchemy import inspect, text


os.environ['SKIP_DATABASE_BOOTSTRAP'] = '1'

from app.main import create_app  # noqa: E402
from app.models.job import JobNotification, JobSource  # noqa: E402
from app.models.service import PlatformSetting  # noqa: E402
from app.utils.attachment_retention import purge_historical_client_attachments  # noqa: E402
from app.utils.database import db  # noqa: E402


ATTACHMENT_RETENTION_MARKER = 'historical_attachment_cleanup_20260907'


def prepare_additive_job_tables():
    app = create_app()
    with app.app_context():
        inspector = inspect(db.engine)
        if 'alembic_version' not in inspector.get_table_names():
            print('Fresh database detected; Alembic will create the complete schema.')
            return False
        current = db.session.execute(text('SELECT version_num FROM alembic_version')).scalar()
        if current != '20260831_13':
            print(f'No job-table preflight needed at database revision {current or "unknown"}.')
            return False
        JobSource.__table__.create(bind=db.engine, checkfirst=True)
        JobNotification.__table__.create(bind=db.engine, checkfirst=True)
        print('Additive job-feed tables are ready for migration revision 20260831_14.')
        return True


def run_historical_attachment_cleanup():
    """Apply the legacy closed-order retention rule exactly once when enabled."""
    if os.getenv('RUN_HISTORICAL_ATTACHMENT_PURGE') != '1':
        return None

    app = create_app()
    with app.app_context():
        marker = db.session.get(PlatformSetting, ATTACHMENT_RETENTION_MARKER)
        if marker and marker.value.startswith('completed'):
            print('Historical client-document retention cleanup already completed; skipping.')
            return {'mode': 'already-completed'}

        result = purge_historical_client_attachments(apply=True)
        if result['failed_attachments']:
            raise RuntimeError(
                f"Historical attachment cleanup failed for {result['failed_attachments']} attachment(s); "
                'the deployment is stopping so the maintenance can be retried safely.'
            )

        value = f"completed:{result['deleted_attachments']}"
        if marker is None:
            marker = PlatformSetting(key=ATTACHMENT_RETENTION_MARKER, value=value)
            db.session.add(marker)
        else:
            marker.value = value
        db.session.commit()
        print(
            'Historical client-document retention cleanup completed: '
            f"{result['deleted_attachments']} attachment(s) deleted across "
            f"{result['matched_orders']} closed request(s)."
        )
        return result


if __name__ == '__main__':
    prepare_additive_job_tables()
    run_historical_attachment_cleanup()
