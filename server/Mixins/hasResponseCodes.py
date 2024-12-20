import re
from abc import ABCMeta, abstractmethod
from Classes.Vector3 import Vector3
from globals import current_app

class hasResponsecodes(metaclass=ABCMeta):
    headPosition: Vector3 = None

    @abstractmethod
    def getPrintTime(self):
        pass

    @abstractmethod
    def getToolHeadLocation(self) -> Vector3:
        pass

def checkOK(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return "ok" in line

def checkXYZ(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return ("x:" in line) and ("y:" in line) and ("z:" in line)

def checkEcho(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return line.startswith("echo")

def checkBedTemp(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    try:
        return checkTemp([temp.strip() for temp in line.split("b:")[1].split("t0:")[0].split("x:")[0].split("/")], dev)
    except IndexError:
        return False
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkExtruderTemp(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    try:
        return checkTemp([temp.strip() for temp in line.split("T:")[1].split("B:")[0].split("/")], dev)
    except IndexError:
        return False
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkTemp(temps, dev):
    try:
        if len(temps) == 2:
            if float(temps[1]) == 0.0: return True
            return abs(float(temps[1]) - float(temps[0])) < 0.25
        return False
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkTime(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return re.search(r"\d+m \d+s", line) or re.search(r"\d+ min, \d+ sec", line)