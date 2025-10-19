import logging
import traceback
from Classes.Loggers.ABCLogger import ABCLogger

class ErrorService:
    @staticmethod
    def handle_errors_and_logging(e: Exception | str, logger=None, level=logging.ERROR):
        """
        Handles errors and logs them
        :param Exception | str e: the exception to handle
        :param ABCLogger | None logger: the logger to use
        :param int level: the logging level
        """
        if logger is not None:
            logger.log(level, e, stacklevel=5)
        elif logger is None:
            if isinstance(e, str):
                print(e.strip())
            else:
                print(traceback.format_exception(None, e, e.__traceback__))
        else:
            logger.log(level, e, stacklevel=5)
        return False