import logging
import os
import sys
import shutil
from Classes.Loggers.Logger import Logger
from config.paths import root_path
from werkzeug.serving import WSGIRequestHandler
from flask import current_app

class LoggingService:
    def __init__(self, app):
        self.app = app
        self.setup_werkzeug_logging()
        self.logger = self.setup_custom_logging()
        
    def setup_werkzeug_logging(self):
        """Setup werkzeug logging to output to stdout."""
        # Get the werkzeug logger
        logger = logging.getLogger('werkzeug')
        # Change the output stream to stdout
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(sys.stdout)
        
        # Ensure Werkzeug's request handler also logs to stdout
        WSGIRequestHandler.log = lambda self, type, message, *args: print(
            f"{self.address_string().replace('%', '%%')} - - [{self.log_date_time_string()}] {message % args}",
            file=sys.stdout)
    
    def setup_custom_logging(self):
        """Setup custom application logger."""
        logs = os.path.join(root_path, "logs")
        os.makedirs(logs, exist_ok=True)
        
        return Logger("App", 
                     consoleLogger=sys.stdout, 
                     fileLogger=os.path.abspath(os.path.join(logs, "QViewApp.log")),
                     consoleLevel=logging.ERROR)
    
    def get_logger(self):
        return self.logger

def cleanup_directories():
    """
    Clean up and recreate upload and temporary directories.
    
    Removes existing uploads and tempcsv folders and recreates them as empty directories.
    This ensures a clean state on application startup.
    """
    try:
        uploads_folder = os.path.abspath('../uploads')
        tempcsv = os.path.abspath('../tempcsv')
        
        for folder in [uploads_folder, tempcsv]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                current_app.logger.info(f"{folder} removed and will be recreated.")
            os.makedirs(folder)
            current_app.logger.info(f"{folder} recreated as an empty directory.")
            
    except Exception as e:
        current_app.handle_errors_and_logging(e)