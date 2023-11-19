from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from decouple import config
from routes.display import display_bp
from tasks.main import main
from database.connectdb import init_db  # Import the init_db function
from database.setup import setup_database
from Classes import serialCommunication
from Classes.PrinterList import PrinterList

app = Flask(__name__)

DB_HOST = config('DB_HOST')
DB_USER = config('DB_USER')
DB_PASSWORD = config('DB_PASSWORD')
DB_NAME = config('DB_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'

db = init_db(app)  # Initialize db with the Flask app

# Register the display_bp Blueprint
app.register_blueprint(display_bp)
app.register_blueprint(main)
    
with app.app_context(): # initialization code: Creates list of printers 
    print("Initializing Printer objects...")
    connectedPrinters = serialCommunication.get3DPrinterList()
    printerObjects = PrinterList(connectedPrinters)

if __name__ == "__main__":
    # setup.setup_database()
    app.run(port=8000, debug=True)
    
