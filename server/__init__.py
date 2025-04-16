import os
from flask import Flask
from dotenv import load_dotenv
from pathlib import Path
from . import db

#load .env file from root directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# create and configure the app
app = Flask(__name__)

# Load configuration from environment variables
app.config.from_mapping(
    SERVER_IP_ADDRESS=os.environ.get('SERVER_IP_ADDRESS'),
    SERVER_PORT=os.environ.get('SERVER_PORT'),
)

# initialize the database
db.init_app(app)

# define a test route to check if the server is running
@app.route('/')
def test():
    return 'Server is running'

@app.route('/test_db_conn')
def test_db_conn():
    try:
        db.get_db()
        return 'Database connection successful'
    except Exception as e:
        return f'Database connection failed: {str(e)}'