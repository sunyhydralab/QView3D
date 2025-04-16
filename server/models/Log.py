from enum import Enum

# Enumeration for log types.
class LogType(Enum):
    ERROR = 0
    INFO = 1

'''Attributes: 
    id (int): Unique identifier for the log.
    content (str): Log message, 4096 character limit.
    job_id (int): Reference to job it's in.
    type (LogType): Type of log (i.e. error, info).
'''
class Log: 
    def __init__(
            self, id: int, 
            content: str, 
            job_id: int, 
            type: LogType
        ):
        self.id = id
        self.content = content
        self.job_id = job_id
        self.type = type

    # Developer representation of the logs.
    def __repr__(self):
        return (
            f"id={self.id}, job_id={self.job_id}, type={self.type.value},"
            f"content={self.content}"
        )