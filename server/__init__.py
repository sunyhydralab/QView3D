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
    SECRET_KEY=os.getenv('SECRET_KEY'),
    DATABASE=os.path.join(".","server" , os.getenv('DATABASE_NAME'))
)

# initialize the database
db.init_app(app)

# define a test route to check if the server is running
@app.route('/')
def test():
    return 'Server is running'