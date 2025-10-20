"""Database logger for QView3D"""
import os
from datetime import datetime

class Logger:
    """Logger for all operations - saves to database when needed"""

    # Logging levels (matching Python's logging module)
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
        """Log message - only saves if debug mode"""
        if self.debug:
            entry = f"[{datetime.now().strftime('%H:%M:%S')}] {level}: {message}"
            self.logs.append(entry)
            print(entry)

    def error(self, message, exc=None):
        """Always log errors"""
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] ERROR: {message}"
        if exc:
            entry += f" - {str(exc)}"
        self.logs.append(entry)
        if self.debug:
            print(entry)

    def get_logs(self):
        """Get all logs for database storage"""
        return "\n".join(self.logs)

    def clear(self):
        """Clear logs"""
        self.logs = []

# Global logger instance
logger = Logger()