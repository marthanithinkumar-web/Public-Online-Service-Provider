"""Prepare the one additive job-feed migration on an existing production DB.

Production was already at revision 20260831_13 before the job feed shipped.
Creating the two new tables with SQLAlchemy's check-first DDL makes revision 14
safe to record even if a managed deployment previously stopped during that
additive migration. Fresh databases and any other revision use Alembic alone.
"""

import os

from sqlalchemy import inspect, text


os.environ['SKIP_DATABASE_BOOTSTRAP'] = '1'

from app.main import create_app  # noqa: E402
from app.models.job import JobNotification, JobSource  # noqa: E402
from app.utils.database import db  # noqa: E402


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


if __name__ == '__main__':
    prepare_additive_job_tables()
