"""Simplified logging service - lean and mean"""
import logging
from services.logger import logger

class LoggingService:
    """Minimal logging service for Flask app"""

    def __init__(self, app):
        self.app = app
        self.logger = logger

        # Silence werkzeug unless in debug mode
        if not logger.debug:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

    def get_logger(self):
        return self.logger