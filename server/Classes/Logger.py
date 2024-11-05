import logging
import os
import sys
import traceback

from _pytest._code.code import ExceptionChainRepr


class Logger(logging.Logger):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, port, deviceName, consoleLogger=sys.stdout, fileLogger=None):
        super().__init__(f"Logger_{port}_{deviceName}")
        console_handler = logging.StreamHandler(consoleLogger)
        console_handler.setFormatter(CustomFormatter("%(asctime)s - %(message)s"))
        self.addHandler(console_handler)
        self.setLevel(logging.INFO)  # Adjust this as needed
        if fileLogger is None:
            log_folder = "./server/logs"
            os.makedirs(log_folder, exist_ok=True)
            subfolder = os.path.join(log_folder, port)
            os.makedirs(subfolder, exist_ok=True)
            fileLogger = logging.FileHandler(os.path.join(subfolder, f"test_{port}.log"))
        else:
            fileLogger = logging.FileHandler(fileLogger)
        fileLogger.setFormatter(logging.Formatter("%(message)s"))
        self.addHandler(fileLogger)
        self.setLevel(logging.INFO)  # Adjust this as needed

    def formatLog(self, msg):
        if isinstance(msg, str):
            pass
        elif isinstance(msg, Exception):
            msg = traceback.format_exception(msg.__traceback__)
        elif isinstance(msg, ExceptionChainRepr):
            msg = msg.reprtraceback.__repr__()
        elif isinstance(msg, list) or isinstance(msg, tuple):
            msgList = msg
            msg = ""
            for line in msgList:
                msg += self.formatLog(line)
        else:
            msg = str(msg)
        return msg

    def info(self, msg: str | Exception | ExceptionChainRepr, *args, end='', **kwargs):
        """Log a message with level INFO and append `end` after the message."""
        msg = self.formatLog(msg)
        super().info(msg + end, *args, **kwargs)

    def debug(self, msg: str | Exception | ExceptionChainRepr, *args, end='', **kwargs):
        """Log a message with level DEBUG and append `end` after the message."""
        msg = self.formatLog(msg)
        super().debug(msg + end, *args, **kwargs)

    def warning(self, msg: str | Exception | ExceptionChainRepr, *args, end='', **kwargs):
        """Log a message with level WARNING and append `end` after the message."""
        msg = self.formatLog(msg)
        super().warning(msg + end, *args, **kwargs)

    def error(self, msg: str | Exception | ExceptionChainRepr, *args, end='', **kwargs):
        """Log a message with level ERROR and append `end` after the message."""
        msg = self.formatLog(msg)
        super().error(msg + end, *args, **kwargs)

    def critical(self, msg: str | Exception | ExceptionChainRepr, *args, end='', **kwargs):
        """Log a message with level CRITICAL and append `end` after the message."""
        msg = self.formatLog(msg)
        super().critical(msg + end, *args, **kwargs)

    def logMessageOnly(self, msg: str, logLevel: int = None, *args, **kwargs):
        if logLevel is None:
            logLevel = self.level
        """Log a message without any additional formatting."""
        oldFormatters = [handler.formatter for handler in self.handlers]
        for handler in self.handlers:
            handler.setFormatter(CustomFormatter("%(message)s"))
        if logLevel == self.DEBUG:
            self.debug(msg, *args, **kwargs)
        elif logLevel == self.INFO:
            self.info(msg, *args, **kwargs)
        elif logLevel == self.WARNING:
            self.warning(msg, *args, **kwargs)
        elif logLevel == self.ERROR:
            self.error(msg, *args, **kwargs)
        elif logLevel == self.CRITICAL:
            self.critical(msg, *args, **kwargs)
        for handler, formatter in zip(self.handlers, oldFormatters):
            handler.setFormatter(formatter)

class CustomFormatter(logging.Formatter):
    # ANSI escape codes for colors
    COLOR_CODES = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[0m",  # white
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m"  # Magenta
    }
    RESET_CODE = "\033[0m"  # Reset to default color

    def format(session, record):
        # Apply color based on log level
        color = session.COLOR_CODES.get(record.levelname, session.RESET_CODE)
        message = super().format(record)
        return f"{color}{message}{session.RESET_CODE}"
