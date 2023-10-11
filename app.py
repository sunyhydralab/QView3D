from flask import Flask
from decouple import config
from database import setup
from routes.display import display_bp  # Import the Blueprint
from routes.formhandling import formhandling_bp

app = Flask(__name__)

DB_HOST = config('DB_HOST')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_NAME = config('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

# Register the display_bp Blueprint
app.register_blueprint(display_bp)
app.register_blueprint(formhandling_bp)

if __name__ == "__main__":
    # setup.setup_database()
    app.run(port=8000, debug=True)