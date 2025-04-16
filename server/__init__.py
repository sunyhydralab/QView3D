import os
from flask import Flask
from dotenv import load_dotenv
from pathlib import Path

#load .env file from root directory
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# create and configure the app
app = Flask(__name__)

# Load configuration from environment variables
app.config.from_mapping(
    SECRET_KEY=os.getenv('SECRET_KEY'),
    DATABASE=os.getenv('DATABASE')
)

# define a test route to check if the server is running
@app.route('/')
def test():
    return 'Server is running'