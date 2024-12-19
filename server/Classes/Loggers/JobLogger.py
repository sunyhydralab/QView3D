import logging
import os
import shutil
from os import PathLike
from typing import TextIO

from Classes.Loggers.ABCLogger import ABCLogger, CustomColorFormatter, CustomFileHandler

class JobLogger(ABCLogger):
    fileLogger: str | PathLike = None
    fileLoggers = {"CRITICAL": ABCLogger.CRITICAL, "ERROR": ABCLogger.ERROR, "WARNING": ABCLogger.WARNING, "INFO": ABCLogger.INFO, "DEBUG": ABCLogger.DEBUG}

    def __init__(self, deviceName, jobName, startTime, port=None, consoleLogger: TextIO | None = None, fileLogger=None, loggingLevel=logging.INFO, showFile=True, showLevel=True, showDate=True):
        """
        :param str deviceName: The name of the device
        :param str jobName: The name of the job
        :param str startTime: The time the job started
        :param str | None port: com port of device
        :param TextIO | None consoleLogger: The console to output to
        :param str | None fileLogger: File path to log to create all logs in
        :param int loggingLevel: Logging level
        :param bool showFile: whether to show the file in each log line
        :param bool showLevel: whether to show the level in each log line
        :param bool showDate: whether to show the date in each log line
        """
        title = []
        if port:
            title.append(port)
        if deviceName:
            title.append(deviceName)
        super().__init__(f"_".join(["JobLogger"] + title))
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
            consoleLogger.setFormatter(CustomColorFormatter(formatString))
            self.consoleLogger = consoleLogger
            self.addHandler(consoleLogger)
        else: self.consoleLogger = None

        # create the file loggers
        if fileLogger is None:
            from globals import root_path
            fileLogger = os.path.abspath(os.path.join(root_path, "logs", deviceName, jobName, startTime))
            os.makedirs(fileLogger, exist_ok=True)
        else:
            os.makedirs(fileLogger, exist_ok=True)
        self.fileLogger = fileLogger
        for file in self.fileLoggers.keys():
            colorLogger =  os.path.join(fileLogger, "color", file + ".log")
            noColorLogger = os.path.join(fileLogger,"no color", file + ".log")
            os.makedirs(os.path.dirname(colorLogger), exist_ok=True)
            os.makedirs(os.path.dirname(noColorLogger), exist_ok=True)
            colorLogger = CustomFileHandler(colorLogger, mode="w")
            noColorLogger = CustomFileHandler(noColorLogger, mode="w")
            colorLogger.setFormatter(CustomColorFormatter(formatString))
            noColorLogger.setFormatter(logging.Formatter(formatString))
            level = self.fileLoggers[file]
            colorLogger.setLevel(level)
            noColorLogger.setLevel(level)
            self.addHandler(colorLogger)
            self.addHandler(noColorLogger)

    def setLevel(self, level):
        """
        Set the logging level for the logger and its handlers.
        :param int level: The logging level, 10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL
        """
        if self.consoleLogger is not None: self.consoleLogger.setLevel(level)


    def nukeLogs(self):
        """Delete all the logs created by the logger, then clear the directories in the log path that are empty."""
        for handler in self.handlers:
            if isinstance(handler, CustomFileHandler):
                handler.close()
                os.remove(handler.baseFilename)
        while self.fileLogger is not None and os.path.isdir(self.fileLogger):
            # Check if fileLogger directory is empty (excluding subdirectories)
            if not any(os.path.isfile(os.path.join(self.fileLogger, f)) for f in os.listdir(self.fileLogger)):
                shutil.rmtree(self.fileLogger)  # Remove the empty directory
                self.fileLogger = os.path.dirname(self.fileLogger)  # Move to the parent directory
            else:
                break  # Stop if the directory contains any files


