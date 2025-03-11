import os
import sys
from typing import TextIO
from Classes.Loggers.ABCLogger import ABCLogger, CustomColorFormatter, CustomFileHandler, CustomFormatter

class Logger(ABCLogger):
    def __init__(self, deviceName, port=None, consoleLogger=sys.stdout, fileLogger=None, loggingLevel=ABCLogger.INFO, showFile=True, showLevel=True, showDate=True, consoleLevel=None):
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
        super().setLevel(ABCLogger.DEBUG)
        info = []
        if showDate:
            info.append("%(asctime)s")
        if showLevel:
            info.append("%(levelname)s")
        if showFile:
            info.append("%(module)s.%(funcName)s:%(lineno)d")
        formatString = " - ".join(info + ["%(message)s"])
        if consoleLogger is not None:
            consoleLogger = ABCLogger.StreamHandler(consoleLogger)
            if consoleLevel is not None:
                consoleLogger.setLevel(consoleLevel)
            else:
                consoleLogger.setLevel(loggingLevel)
            consoleLogger.setFormatter(CustomColorFormatter(formatString, file=False))
            self.consoleLogger = consoleLogger
            self.addHandler(consoleLogger)
        else: self.consoleLogger = None
        if fileLogger is None:
            from globals import root_path
            log_folder = os.path.abspath(os.path.join(root_path,"logs", deviceName))
            os.makedirs(log_folder, exist_ok=True)
            fileLogger = CustomFileHandler(os.path.join(log_folder, "fabricator.log"))
        else:
            if not os.path.exists(fileLogger):
                fileLogger = CustomFileHandler(fileLogger, mode='w')
            else:
                fileLogger = CustomFileHandler(fileLogger)
        fileLogger.setFormatter(CustomFormatter(formatString, file=True))
        fileLogger.setLevel(loggingLevel)
        self.fileLogger = fileLogger
        self.addHandler(fileLogger)
