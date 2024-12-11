import logging
import os
import sys
import traceback
from typing import TextIO

from _pytest._code.code import ExceptionChainRepr, ReprEntry, ReprEntryNative
from _pytest.fixtures import FixtureLookupErrorRepr
from typing_extensions import Sequence


class Logger(logging.Logger):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, deviceName, port=None, consoleLogger=sys.stdout, fileLogger=None, loggingLevel=logging.INFO, showFile=True, showLevel=True, showDate=True, consoleLevel=None):
        """
        Initialize a logger for a device with a console and file handler.
        :param str deviceName: The name of the device
        :param str port: com port of device
        :param TextIO consoleLogger: The console to output to
        :param str fileLogger: File path to log to
        :param int loggingLevel: Logging level
        :param bool showFile: whether to show the file in each log line
        :param bool showLevel: whether to show the level in each log line
        :param bool showDate: whether to show the date in each log line
        :param consoleLevel: The level to log to the console, this is to allow for different levels to be logged to the console and file.
        """
        title = []
        if port:
            title.append(port)
        if deviceName:
            title.append(deviceName)
        super().__init__(f"_".join(["Logger"] + title))
        super().setLevel(loggingLevel)
        info = []
        if showDate:
            info.append("%(asctime)s")
        if showLevel:
            info.append("%(levelname)s")
        if showFile:
            info.append("%(module)s.%(funcName)s:%(lineno)d")
        formatString = " - ".join(info + ["%(message)s"])
        if consoleLogger is not None:
            consoleLogger = logging.StreamHandler(consoleLogger)
            if consoleLevel is not None:
                consoleLogger.setLevel(consoleLevel)
            else:
                consoleLogger.setLevel(loggingLevel)
            consoleLogger.setFormatter(CustomFormatter(formatString))
            self.consoleLogger = consoleLogger
            self.addHandler(consoleLogger)
        else: self.consoleLogger = None
        if fileLogger is None:
            from globals import root_path
            log_folder = os.path.abspath(os.path.join(root_path, "server","logs"))
            os.makedirs(log_folder, exist_ok=True)
            subfolder = os.path.join(log_folder, deviceName)
            os.makedirs(subfolder, exist_ok=True)
            fileLogger = CustomFileHandler(os.path.join(subfolder, "fabricator.log"))
        else:
            if not os.path.exists(fileLogger):
                fileLogger = CustomFileHandler(fileLogger, mode='w')
            else:
                fileLogger = CustomFileHandler(fileLogger)
        fileLogger.setFormatter(CustomFormatter(formatString))
        fileLogger.setLevel(loggingLevel)
        self.fileLogger = fileLogger
        self.addHandler(fileLogger)

    @staticmethod
    def formatLog(msg):
        """
        Format the log message.
        :param str | ExceptionChainRepr | Exception | list | tuple msg: input to format
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

    def info(self, msg: str | Exception | ExceptionChainRepr | list | tuple, end='', stacklevel: int = 2, *args, **kwargs):
        """
        Log a message with level INFO and append `end` after the message.
        :param str | Exception | ExceptionChainRepr | list | tuple msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().info(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def debug(self, msg: str | Exception | ExceptionChainRepr | list | tuple, end='', stacklevel: int = 2, *args, **kwargs):
        """
        Log a message with level DEBUG and append `end` after the message.
        :param str | Exception | ExceptionChainRepr | list | tuple msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().debug(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def warning(self, msg: str | Exception | ExceptionChainRepr | list | tuple, end='', stacklevel: int = 2, *args, **kwargs):
        """
        Log a message with level WARNING and append `end` after the message.
        :param str | Exception | ExceptionChainRepr | list | tuple msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().warning(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def error(self, msg: str | Exception | ExceptionChainRepr | list | tuple, end='', stacklevel: int = 2, *args, **kwargs):
        """
        Log a message with level ERROR and append `end` after the message.
        :param str | Exception | ExceptionChainRepr | list | tuple msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().error(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def critical(self, msg: str | Exception | ExceptionChainRepr | list | tuple, end='',stacklevel: int = 2, *args, **kwargs):
        """
        Log a message with level CRITICAL and append `end` after the message.
        :param str | Exception | ExceptionChainRepr | list | tuple msg: The message to log
        :param str end: The string to append to the message
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        msg = self.formatLog(msg)
        super().critical(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def logMessageOnly(self, msg: str, logLevel: int = None, stacklevel: int = 3, *args, **kwargs):
        """
        Log a message without any additional formatting, removing the log level, date, time, and file info.
        :param str msg: the message to log
        :param int logLevel: the level to log the message at
        :param int stacklevel: The level in the stack to log from. this is to stop the logger from logging from the logger itself.
        """
        if logLevel is None:
            logLevel = self.level
        """Log a message without any additional formatting."""
        oldFormatters = [handler.formatter for handler in self.handlers]
        for handler in self.handlers:
            handler.setFormatter(CustomFormatter("%(message)s"))
        if logLevel == self.DEBUG:
            self.debug(msg, stacklevel=stacklevel, *args, **kwargs)
        elif logLevel == self.INFO:
            self.info(msg, stacklevel=stacklevel, *args, **kwargs)
        elif logLevel == self.WARNING:
            self.warning(msg, stacklevel=stacklevel, *args, **kwargs)
        elif logLevel == self.ERROR:
            self.error(msg, stacklevel=stacklevel, *args, **kwargs)
        elif logLevel == self.CRITICAL:
            self.critical(msg, stacklevel=stacklevel, *args, **kwargs)
        for handler, formatter in zip(self.handlers, oldFormatters):
            handler.setFormatter(formatter)

    def logException(self, reprentries: list[ExceptionChainRepr] | ExceptionChainRepr | list[ReprEntry | ReprEntryNative] | Sequence[ReprEntry | ReprEntryNative]| list[FixtureLookupErrorRepr] | FixtureLookupErrorRepr | ReprEntry | str):
        """
        Log an exception chain, for use in pytests.
        :param list[ExceptionChainRepr] | ExceptionChainRepr | list[ReprEntry | ReprEntryNative] | Sequence[ReprEntry | ReprEntryNative]| list[FixtureLookupErrorRepr] | FixtureLookupErrorRepr | ReprEntry | str reprentries: The exception chain to log
        """
        if isinstance(reprentries, ExceptionChainRepr) or isinstance(reprentries, ReprEntry) or isinstance(reprentries, FixtureLookupErrorRepr):
            reprentries = [reprentries]
        if isinstance(reprentries, list):
            for index, reprentry in enumerate(reprentries):
                if isinstance(reprentry, ReprEntry):
                    if reprentry.reprfuncargs is not None:
                        things = list(reprentry.reprfuncargs.args)
                        for args in things:
                            self.logMessageOnly(f"{args[0]} = {args[1]}")
                            self.logMessageOnly("")
                    for line in list(reprentry.lines):
                        if line.startswith("E") or line.startswith(">"):
                            self.logMessageOnly(line.__str__(), logLevel=self.ERROR)
                        else:
                            self.logMessageOnly(line.__str__())
                    loc = reprentry.reprfileloc
                    self.logMessageOnly("\n" + loc.path + ":" + loc.lineno.__str__() + ": " + loc.message, logLevel=self.ERROR)
                elif isinstance(reprentry, ExceptionChainRepr):
                    chain = reprentry.chain
                    for link in chain:
                        self.logException(link[0].reprentries)
                elif isinstance(reprentry, FixtureLookupErrorRepr):
                    for line in reprentry.tblines:
                        self.logMessageOnly(line.rstrip())
                    lines = reprentry.errorstring.split("\n")
                    if lines:
                        for line in lines:
                            if line.startswith("E") or line.startswith(">"):
                                self.logMessageOnly(line, logLevel=self.ERROR)
                            else:
                                self.logMessageOnly(line)

                if index < len(reprentries) - 1:
                    from conftest import line_separator
                    self.logMessageOnly(line_separator("", symbol="- "), logLevel=self.INFO)
        elif isinstance(reprentries, str):
            for line in reprentries.split("\n"):
                if line.startswith("E") or line.startswith(">"):
                    self.logMessageOnly(line, logLevel=self.ERROR)
                else:
                    self.logMessageOnly(line)

    def setLevel(self, level):
        """
        Set the logging level for the logger and its handlers.
        :param int level: The logging level, 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL
        """
        super().setLevel(level)
        if self.consoleLogger is not None: self.consoleLogger.setLevel(level)
        self.fileLogger.setLevel(level)

class CustomFormatter(logging.Formatter):
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

class CustomFileHandler(logging.FileHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            self.stream.write(msg + "\n")
            self.flush()
        except RecursionError:
            pass
