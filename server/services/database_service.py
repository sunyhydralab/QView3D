import os
from flask_migrate import Migrate
from config.db import db
from config.config import Config
from globals import root_path

class DatabaseService:
    def __init__(self, app):
        self.app = app
        self.setup_database()
    
    def setup_database(self):
        """Setup database configuration and initialize SQLAlchemy."""
        # Database configuration
        basedir = os.path.abspath(os.path.join(root_path, "server"))
        database_file = os.path.abspath(os.path.join(basedir, Config.get('database_uri')))
        if isinstance(database_file, bytes):
            database_file = database_file.decode('utf-8')
        
        databaseuri = 'sqlite:///' + database_file
        self.app.config['SQLALCHEMY_DATABASE_URI'] = databaseuri
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize database
        db.init_app(self.app)
        Migrate(self.app, db)