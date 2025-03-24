from abc import ABCMeta, abstractmethod

class hasStartupSequence(metaclass=ABCMeta):
    @abstractmethod
    def startupSequence(self):
        pass
