from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS
import os
from models.db import db
from models.PrinterStatusService import PrinterStatusService
from flask_migrate import Migrate
from dotenv import load_dotenv
from controllers.ports import getRegisteredFabricators
import shutil
from flask_socketio import SocketIO
from models.config import Config


# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup 
app = Flask(__name__, static_folder='../client/dist')
app.config.from_object(__name__) # update application instantly
logs = os.path.join('./logs')
from Classes.Logger import Logger
app.logger = Logger("App", consoleLogger=None, fileLogger=os.path.join(logs, "app.log"))
# start database connection
app.config["environment"] = Config.get('environment')
app.config["ip"] = Config.get('ip')
app.config["port"] = Config.get('port')
app.config["base_url"] = Config.get('base_url')

load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
database_file = os.path.join(basedir, Config.get('database_uri'))
if isinstance(database_file, bytes):
    database_file = database_file.decode('utf-8')
databaseuri = 'sqlite:///' + database_file
app.config['SQLALCHEMY_DATABASE_URI'] = databaseuri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

migrate = Migrate(app, db)
# moved this before importing the blueprints so that it can be accessed by the PrinterStatusService
printer_status_service = PrinterStatusService(app)

# Initialize SocketIO, which will be used to send printer status updates to the frontend
# and this specific socket it will be used throughout the backend

if app.config["environment"] == 'production':
    async_mode = 'eventlet'  # Use 'eventlet' for production
else:
    async_mode = 'threading'  # Use 'threading' for development

socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False, async_mode=async_mode) # make it eventlet on production!
app.socketio = socketio  # Add the SocketIO object to the app object

def handle_errors_and_logging(e: Exception, fabricator = None):
    from Classes.Fabricators.Fabricator import Fabricator
    device = fabricator
    if isinstance(fabricator, Fabricator):
        device = fabricator.device
    if device.logger is None:
        if app.logger is None:
            print(e)
        else:
            app.logger.error("Error:")
            app.logger.error(e)
    else:
        device.logger.error("Error:")
        device.logger.error(e)
    return True

app.handle_error_and_logging = handle_errors_and_logging

CORS(app)

@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        res = Response()
        res.headers['X-Content-Type-Options'] = '*'
        res.headers['Access-Control-Allow-Origin'] = '*'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return res

# Serve static files
@app.route('/')
def serve_static(path='index.html'):
    return send_from_directory(app.static_folder, path)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

# IMPORTING BLUEPRINTS
from controllers.ports import ports_bp
from controllers.jobs import jobs_bp
from controllers.statusService import status_bp
from controllers.issues import issue_bp

# # Register the display_bp Blueprint
app.register_blueprint(ports_bp)
app.register_blueprint(jobs_bp)
app.register_blueprint(status_bp)
app.register_blueprint(issue_bp)
    
@app.socketio.on('ping')
def handle_ping():
    app.socketio.emit('pong')

# own thread
with app.app_context():
    try:
        # Create in-memory uploads folder
        uploads_folder = os.path.join('../uploads')
        tempcsv = os.path.join('../tempcsv')

        # Creating printer threads from registered printers on server start 
        res = getRegisteredFabricators() # gets registered fabricators from DB
        data = res[0].get_json() # converts to JSON 
        printers_data = data.get("printers", []) # gets the values w/ printer data
        printer_status_service.create_printer_threads(printers_data)

        if os.path.exists(uploads_folder):
            # Remove the uploads folder and all its contents
            shutil.rmtree(uploads_folder)
            shutil.rmtree(tempcsv)

            # Recreate it as an empty directory
            os.makedirs(uploads_folder)
            os.makedirs(tempcsv)

            app.logger.info("Uploads folder recreated as an empty directory.")
        else:
            # Create the uploads folder if it doesn't exist
            os.makedirs(uploads_folder)
            os.makedirs(tempcsv)
            app.logger.info("Uploads folder created successfully.")
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
            

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    socketio.run(app, debug=True)  # Replace app.run with socketio.run