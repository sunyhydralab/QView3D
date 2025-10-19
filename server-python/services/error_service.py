"""Simplified error service"""
import traceback
from services.logger import logger

class ErrorService:
    @staticmethod
    def handle_errors_and_logging(e, log_instance=None, level=None):
        """Simple error handler"""
        error_msg = str(e) if isinstance(e, Exception) else e

        # Use provided logger or global
        log = log_instance or logger

        # Log error with traceback in debug mode
        if logger.debug:
            log.error(error_msg, exc=traceback.format_exc())
        else:
            log.error(error_msg)

        return False