from abc import ABCMeta, abstractmethod

class canPause(metaclass=ABCMeta):
    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is canPause:
            if any("pause" in B.__dict__ for B in subclass.__mro__):
                return True
        return NotImplemented