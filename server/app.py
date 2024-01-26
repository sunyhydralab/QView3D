from flask import Flask, jsonify, request, Response, url_for
from flask_cors import CORS 
import os 
from models.db import db
from models.printers import Printer
from models.jobs import Job
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


# on server start, create a Printer object for each printer in the database and assign it to its 
# own thread     
with app.app_context():
    try:
        res = getRegisteredPrinters() # gets registered printers 
        data = res[0].get_json() # converts to JSON 
        printers_data = data.get("printers", []) # gets the values w/ printer data
        
        printer_objects = []
        
        # Create a Printer object for each printer in printers_data
        for printer_info in printers_data:
            printer = Printer(
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
                status=printer_info["status"],
            )
            printer_objects.append(printer)
            
            for p in printer_objects: 
                print(p.getDevice(p))
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    app.run(port=8000, debug=True)
    
