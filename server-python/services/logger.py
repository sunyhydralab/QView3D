"""Database logger for QView3D"""
import os
from datetime import datetime

class Logger:
    """Logger for all operations - saves to database when needed"""

    def __init__(self, name="QView3D"):
        self.name = name
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.logs = []

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