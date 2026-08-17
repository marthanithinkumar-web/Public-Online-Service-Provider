"""Management script for running migrations and other tasks.
Usage:
  python manage.py db init
  python manage.py db migrate -m "message"
  python manage.py db upgrade
"""
import os
from flask_migrate import MigrateCommand
from flask_script import Manager
from app.main import create_app
from app.utils.database import db

app = create_app()
manager = Manager(app)

# flask-script style; note: flask-script is deprecated but works for simple tasks
try:
    from flask_migrate import Migrate
    migrate = Migrate(app, db)
    # expose 'db' command
    manager.add_command('db', MigrateCommand)
except Exception:
    pass

if __name__ == '__main__':
    manager.run()
