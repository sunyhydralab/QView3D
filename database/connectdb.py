from flask_sqlalchemy import SQLAlchemy
from decouple import config
from sqlalchemy import create_engine

# Create a SQLAlchemy instance
db = SQLAlchemy()
DB_HOST = config('DB_HOST')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_NAME = config('DB_NAME')
engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

def init_db(app):
    # Get database configuration from environment variables or configuration file
    
    # Set the database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
    
    # Initialize the db instance with the Flask app
    db.init_app(app)

    # Return the db instance, so you can use it in other parts of your app
    return db 

