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
from Classes.FabricatorList import FabricatorList


# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup 
app = Flask(__name__, static_folder='../client/dist')
app.config.from_object(__name__) # update application instantly
logs = os.path.join(os.path.dirname(__file__),'logs')
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
fabricator_list = FabricatorList(app)
app.fabricator_list = fabricator_list

# Initialize SocketIO, which will be used to send printer status updates to the frontend
# and this specific socket it will be used throughout the backend

if app.config["environment"] == 'production':
    async_mode = 'eventlet'  # Use 'eventlet' for production
else:
    async_mode = 'threading'  # Use 'threading' for development

socketio = SocketIO(app, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False, async_mode=async_mode) # make it eventlet on production!
app.socketio = socketio  # Add the SocketIO object to the app object

def handle_errors_and_logging(e: Exception | str, fabricator = None):
    from Classes.Fabricators.Fabricator import Fabricator
    device = fabricator
    if isinstance(fabricator, Fabricator):
        device = fabricator.device
    if device is not None and device.logger is not None:
        device.logger.error(e, stacklevel=3)
    elif app.logger is None:
        if isinstance(e, str):
            print(e)
        else:
            import traceback
            print(traceback.format_exception(None, e, e.__traceback__))
    else:
        app.logger.error(e, stacklevel=3)
    return False

app.handle_errors_and_logging = handle_errors_and_logging

CORS(app)

@app.cli.command("test")
def run_tests():
    """Run all tests."""
    import subprocess
    subprocess.run(["python", "../Tests/parallel_test_runner.py"])

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
        # Define directory paths for uploads and tempcsv
        uploads_folder = os.path.abspath('../uploads')
        tempcsv = os.path.abspath('../tempcsv')
        app.FabricatorList = fabricator_list

        # Check if directories exist and handle them accordingly
        for folder in [uploads_folder, tempcsv]:
            if os.path.exists(folder):
                # Remove the folder and all its contents
                import shutil
                shutil.rmtree(folder)
                app.logger.info(f"{folder} removed and will be recreated.")
            # Recreate the folder
            os.makedirs(folder)
            app.logger.info(f"{folder} recreated as an empty directory.")

    except Exception as e:
        # Log any exceptions for troubleshooting
        import traceback
        app.logger.error(f"Unexpected error: {e}")
        app.logger.error(traceback.format_exception(e))

            

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    socketio.run(app, debug=True)  # Replace app.run with socketio.run