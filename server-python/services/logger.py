import os
from datetime import datetime

class Logger:
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __init__(self, name="QView3D", port=None, consoleLogger=None, fileLogger=None, loggingLevel=20, consoleLevel=40):
        self.name = name
        self.port = port
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.logs = []
        self.loggingLevel = loggingLevel
        self.consoleLevel = consoleLevel

    def log(self, message, level="INFO"):
        if self.debug:
            entry = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
            self.logs.append(entry)
            print(entry)

    def error(self, message, exc=None):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {message}"
        if exc:
            entry += f" - {str(exc)}"
        self.logs.append(entry)
        if self.debug:
            print(entry)

    def get_logs(self):
        return "\n".join(self.logs)

    def clear(self):
        self.logs = []

logger = Logger()