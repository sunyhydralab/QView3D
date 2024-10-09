from abc import ABCMeta, abstractmethod

class hasStartupSequence(metaclass=ABCMeta):
    @abstractmethod
    def startupSequence(self):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is hasStartupSequence:
            if any("startupSequence" in B.__dict__ for B in subclass.__mro__):
                return True
        return NotImplemented