import os
from flask_migrate import Migrate
from config.db import db
from config.config import Config

class DatabaseService:
    def __init__(self, app):
        self.app = app
        self.setup_database()

    def setup_database(self):
        basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        database_file = os.path.abspath(os.path.join(basedir, Config.get('database_uri')))
        if isinstance(database_file, bytes):
            database_file = database_file.decode('utf-8')

        os.makedirs(os.path.dirname(database_file), exist_ok=True)

        databaseuri = 'sqlite:///' + database_file
        self.app.config['SQLALCHEMY_DATABASE_URI'] = databaseuri
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        db.init_app(self.app)

        with self.app.app_context():
            db.create_all()

        Migrate(self.app, db)