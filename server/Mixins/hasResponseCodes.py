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

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is hasResponsecodes:
            if any("getPrintTime" in B.__dict__ for B in subclass.__mro__):
                return True
        return NotImplemented


def checkOK(line):
    return line == b'ok\n'

def checkXYZ(line):
    return ("X:" in line) and ("Y:" in line) and ("Z:" in line)