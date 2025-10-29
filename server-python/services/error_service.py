import traceback
from services.logger import logger

class ErrorService:
    @staticmethod
    def handle_errors_and_logging(e, log_instance=None, level=None):
        error_msg = str(e) if isinstance(e, Exception) else e
        log = log_instance or logger

        if logger.debug_mode:
            log.error(error_msg, exc=traceback.format_exc())
        else:
            log.error(error_msg)

        return False