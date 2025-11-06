import logging
from services.logger import logger

class LoggingService:
    def __init__(self, app):
        self.app = app
        self.logger = logger

        if not logger.debug_mode:
            logging.getLogger('werkzeug').setLevel(logging.ERROR)

    def get_logger(self):
        return self.logger