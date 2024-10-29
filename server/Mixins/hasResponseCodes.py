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
    return line == b'ok\n'

def checkXYZ(line):
    line = line.decode("utf-8")
    return ("X:" in line) and ("Y:" in line) and ("Z:" in line)

def alwaysTrue(line):
    return True

def anyResponse(line):
    return line != b''

def checkEcho(line):
    return line.decode("utf-8").startswith("echo")

def checkBedTemp(line):
    try:
        temps = line.decode("utf-8").split("B:")[1].split("X:")[0].split("/")
        if len(temps) == 2:
            if float(temps[1]) == 0.0: return True
            return float(temps[1]) - float(temps[0]) < 0.25
        return True
    except Exception as e:
        return False

def checkExtruderTemp(line):
    try:
        temps = line.decode("utf-8").split("T:")[1].split("B:")[0].split("/")
        if len(temps) == 2:
            if float(temps[1]) == 0.0: return True
            return float(temps[1]) - float(temps[0]) < 0.25
        return True
    except Exception as e:
        return False