import re
import traceback
from abc import ABCMeta, abstractmethod
from Classes.Vector3 import Vector3

class hasResponsecodes(metaclass=ABCMeta):
    headPosition: Vector3 = None

    @abstractmethod
    def getPrintTime(self):
        pass

    @abstractmethod
    def getToolHeadLocation(self) -> Vector3:
        pass

def checkOK(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return line == "ok"

def checkXYZ(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return ("X:" in line) and ("Y:" in line) and ("Z:" in line)

def checkEcho(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return line.startswith("echo")

def checkBedTemp(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    try:
        return checkTemp([temp.strip() for temp in line.split("B:")[1].split("T0:")[0].split("X:")[0].split("/")])
    except IndexError as e:
        return False
    except Exception as e:
        traceback.print_exc()
        return False

def checkExtruderTemp(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    try:
        return checkTemp([temp.strip() for temp in line.split("T:")[1].split("B:")[0].split("/")])
    except IndexError as e:
        return False
    except Exception as e:
        traceback.print_exc()
        return False

def checkTemp(temps):
    try:
        if len(temps) == 2:
            if float(temps[1]) == 0.0: return True
            return float(temps[1]) - float(temps[0]) < 0.25
        return False
    except Exception as e:
        traceback.print_exc()
        return False

def checkTime(line):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return re.search(r"\d+m \d+s", line) or re.search(r"\d+ min, \d+ sec", line)