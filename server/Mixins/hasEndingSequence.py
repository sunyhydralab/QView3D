from abc import abstractmethod, ABCMeta


class hasEndingSequence(metaclass=ABCMeta):
    @abstractmethod
    def endSequence(self):
        pass