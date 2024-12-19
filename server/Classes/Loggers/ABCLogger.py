import logging
import traceback
from abc import ABCMeta

from _pytest._code.code import ExceptionChainRepr


class ABCLogger(logging.Logger, metaclass=ABCMeta):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL
    StreamHandler = logging.StreamHandler
    FileHandler = logging.FileHandler
    Formatter = logging.Formatter
    consoleLogger: StreamHandler | None = None
    fileLogger: FileHandler | None = None

    @staticmethod
    def formatLog(msg):
        """
        Format the log message.
        :param object msg: input to format
        :return: formatted message
        :rtype: str
        """
        if isinstance(msg, str):
            pass
        elif isinstance(msg, ExceptionChainRepr):
            msg = msg.reprtraceback.__repr__()
        elif isinstance(msg, Exception):
            msg = "".join(traceback.format_exception(None, msg, msg.__traceback__))
        elif isinstance(msg, list) or isinstance(msg, tuple):
            msg = "".join(msg)
        else:
            msg = str(msg)
        return msg

    def info(self, msg: object, *args, end: str = '', stacklevel: int = 2, **kwargs):
        """
        Log a message with level INFO and append `end` after the message.
        :param object msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().info(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def debug(self, msg: object, *args, end: str = '', stacklevel: int = 2, **kwargs):
        """
        Log a message with level DEBUG and append `end` after the message.
        :param object msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().debug(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def warning(self, msg: object, *args, end: str = '', stacklevel: int = 2, **kwargs):
        """
        Log a message with level WARNING and append `end` after the message.
        :param object msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().warning(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def error(self, msg: object, *args, end: str = '', stacklevel: int = 2, **kwargs):
        """
        Log a message with level ERROR and append `end` after the message.
        :param object msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().error(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def critical(self, msg: object, *args, end: str = '', stacklevel: int = 2, **kwargs):
        """
        Log a message with level CRITICAL and append `end` after the message.
        :param object msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().critical(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def logMessageOnly(self, msg: str, *args, logLevel: int = None, stacklevel: int = 3, **kwargs):
        """
        Log a message without any additional formatting, removing the log level, date, time, and file info.
        :param str msg: the message to log
        :param int logLevel: the level to log the message at
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        if logLevel is None:
            logLevel = self.level
        oldFormatters = [handler.formatter for handler in self.handlers]
        for handler in self.handlers:
            handler.setFormatter(CustomColorFormatter("%(message)s"))
        self.handleLog(logLevel, msg, *args, stacklevel=stacklevel, **kwargs)
        for handler, formatter in zip(self.handlers, oldFormatters):
            handler.setFormatter(formatter)

    def log(self, level, msg, *args, exc_info=None, stack_info=False, stacklevel: int = 3, extra=None, **kwargs):
        self.handleLog(level, msg, *args, exc_info=exc_info, stack_info=stack_info, stacklevel=stacklevel, extra=extra,
                       **kwargs)

    def handleLog(self, level, msg, *args, exc_info=None, stack_info=False, stacklevel: int = 3, extra=None, **kwargs):
        if level <= self.DEBUG:
            self.debug(msg,*args, stacklevel=stacklevel, exc_info=exc_info, stack_info=stack_info, extra=extra **kwargs)
        elif level <= self.INFO:
            self.info(msg,*args, stacklevel=stacklevel, exc_info=exc_info, stack_info=stack_info, extra=extra **kwargs)
        elif level <= self.WARNING:
            self.warning(msg,*args, stacklevel=stacklevel, exc_info=exc_info, stack_info=stack_info, extra=extra **kwargs)
        elif level <= self.ERROR:
            self.error(msg,*args, stacklevel=stacklevel, exc_info=exc_info, stack_info=stack_info, extra=extra **kwargs)
        elif level <= self.CRITICAL:
            self.critical(msg,*args, stacklevel=stacklevel, exc_info=exc_info, stack_info=stack_info, extra=extra **kwargs)

    def setLevel(self, level):
        """
        Set the logging level for the logger and its handlers.
        :param int level: The logging level, 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL
        """
        super().setLevel(level)
        if self.consoleLogger is not None: self.consoleLogger.setLevel(level)
        if self.fileLogger is not None: self.fileLogger.setLevel(level)


class CustomFileHandler(logging.FileHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + "\n")
            self.flush()
        except RecursionError:
            pass

class CustomColorFormatter(logging.Formatter):
    """
    A custom formatter for the logger, used to apply color to the log messages.
    """
    # ANSI escape codes for colors
    COLOR_CODES = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[0m",  # white
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m"  # Magenta
    }
    RESET_CODE = "\033[0m"  # Reset to default color

    def format(self, record):
        # Apply color based on log level
        color = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        message = super().format(record)
        return f"{color}{message}{self.RESET_CODE}"