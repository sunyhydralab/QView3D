from flask import Flask, jsonify, request, Response, url_for
from threading import Thread
from flask_cors import CORS 
import os 
from models.db import db
from models.printers import Printer
from models.jobs import Job
from models.PrinterStatusService import PrinterStatusService
from flask_migrate import Migrate
from dotenv import load_dotenv
import json 
from controllers.ports import getRegisteredPrinters
#from services.printerStatusService import 
#from services.queueService import 

# IMPORTING BLUEPRINTS 
from controllers.display import display_bp
from controllers.ports import ports_bp
from controllers.jobs import jobs_bp
from controllers.statusService import status_bp, getStatus 

# Basic app setup 
app = Flask(__name__)
app.config.from_object(__name__) # update application instantly 

CORS(app)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        return res

# start database connection
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)

# # Register the display_bp Blueprint
app.register_blueprint(display_bp)
app.register_blueprint(ports_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(status_bp)

# def start_printer_thread(printer):
#     thread = Thread(target=getStatus(printer))
#     thread.start()
#     return thread
printer_status_service = PrinterStatusService()

# on server start, create a Printer object for each printer in the database and assign it to its 
# own thread
with app.app_context():
    try:
        res = getRegisteredPrinters() # gets registered printers 
        data = res[0].get_json() # converts to JSON 
        printers_data = data.get("printers", []) # gets the values w/ printer data
        printer_status_service.create_printer_threads(printers_data)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        
    """
        User should be able to queue a job to a specific printer. Frontend selection -> backend thread -> PrinterInstance.getQueue().addToFront
        
        Also continuously ping specific printer for status 
        
    """
        

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    app.run(port=8000, debug=True)
    
