from abc import ABC, abstractmethod

from Classes.Vector3 import Vector3


class hasResponsecodes(ABC):
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