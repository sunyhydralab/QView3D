import logging
import os
import sys
import traceback
from _pytest._code.code import ExceptionChainRepr, ReprEntry, ReprEntryNative
from _pytest.fixtures import FixtureLookupErrorRepr
from typing_extensions import Sequence


class Logger(logging.Logger):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, deviceName, port=None, consoleLogger=None, fileLogger=None, loggingLevel=logging.INFO, showFile=True, showLevel=True, showDate=True):
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
            consoleLogger.setLevel(loggingLevel)
            consoleLogger.setFormatter(CustomFormatter(formatString))
            self.consoleLogger = consoleLogger
            self.addHandler(consoleLogger)
        if fileLogger is None:
            log_folder = "./server/logs"
            os.makedirs(log_folder, exist_ok=True)
            subfolder = os.path.join(log_folder, deviceName)
            os.makedirs(subfolder, exist_ok=True)
            from datetime import datetime
            fileLogger = logging.FileHandler(os.path.join(subfolder, f"{datetime.now().strftime('%m-%d-%Y__%H-%M-%S')}.log"))
        else:
            if not os.path.exists(fileLogger):
                fileLogger = logging.FileHandler(fileLogger, mode='w')
            else:
                fileLogger = logging.FileHandler(fileLogger)
        fileLogger.setFormatter(logging.Formatter(formatString))
        fileLogger.setLevel(loggingLevel)
        self.fileLogger = fileLogger
        self.addHandler(fileLogger)

    def formatLog(self, msg):
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

    def info(self, msg: str | Exception | ExceptionChainRepr, end='', stacklevel: int = 2, *args, **kwargs):
        """Log a message with level INFO and append `end` after the message."""
        msg = self.formatLog(msg)
        super().info(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def debug(self, msg: str | Exception | ExceptionChainRepr, end='', stacklevel: int = 2, *args, **kwargs):
        """Log a message with level DEBUG and append `end` after the message."""
        msg = self.formatLog(msg)
        super().debug(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def warning(self, msg: str | Exception | ExceptionChainRepr, end='', stacklevel: int = 2, *args, **kwargs):
        """Log a message with level WARNING and append `end` after the message."""
        msg = self.formatLog(msg)
        super().warning(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def error(self, msg: str | Exception | ExceptionChainRepr, end='', stacklevel: int = 2, *args, **kwargs):
        """Log a message with level ERROR and append `end` after the message."""
        msg = self.formatLog(msg)
        super().error(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def critical(self, msg: str | Exception | ExceptionChainRepr, end='',stacklevel: int = 2, *args, **kwargs):
        """Log a message with level CRITICAL and append `end` after the message."""
        msg = self.formatLog(msg)
        super().critical(msg + end, *args, **kwargs, stacklevel=stacklevel)

    def logMessageOnly(self, msg: str, logLevel: int = None, stacklevel: int = 3, *args, **kwargs):
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
        super().setLevel(level)
        self.consoleLogger.setLevel(level)
        self.fileLogger.setLevel(level)

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

    def format(self, record):
        # Apply color based on log level
        color = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        message = super().format(record)
        return f"{color}{message}{self.RESET_CODE}"
