import os, argparse

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from tms.db.db import db_context
from tms.server import app, load_app_config
from tms.server.config import app_config


MIGRATION_DIR = os.path.join('tms', 'db', 'migrations')


migrate = Migrate(app, db_context, directory=MIGRATION_DIR)
manager = Manager(app)

manager.add_option('-l', '--level', dest='level', required=False)
def create_app(level=None):
    app = load_app_config(level)
    print(level)
    return app

manager.add_command('db', MigrateCommand)
if __name__ == '__main__':
    manager.run()


    # Sample commands:
        # create migration based on local DB diff
            # python ./manage.py -l development db migrate

        # upgrade remote db
            # python ./manage.py -l staging db upgrade