from abc import ABCMeta, abstractmethod
from Classes.Vector3 import Vector3

class hasResponsecodes(metaclass=ABCMeta):
    headPosition: Vector3 = None

    @abstractmethod
    def getPrintTime(self):
        pass

    @abstractmethod
    def getPrintHeadLocation(self) -> Vector3:
        pass

def checkOK(line):
    return line == b'ok\n'

def checkXYZ(line):
    return ("X:" in line) and ("Y:" in line) and ("Z:" in line)

def alwaysTrue(line):
    return True