from abc import abstractmethod, ABCMeta


class hasEndingSequence(metaclass=ABCMeta):
    @abstractmethod
    def endSequence(self):
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is hasEndingSequence:
            if any("endSequence" in B.__dict__ for B in subclass.__mro__):
                return True
        return NotImplemented