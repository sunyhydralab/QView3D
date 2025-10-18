from abc import abstractmethod, ABCMeta


class hasEndingSequence(metaclass=ABCMeta):
    @abstractmethod
    def endSequence(self):
        """Define the ending sequence for a fabricator."""
        pass