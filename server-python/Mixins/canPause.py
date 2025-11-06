from abc import ABCMeta, abstractmethod

class canPause(metaclass=ABCMeta):
    @abstractmethod
    def pause(self):
        pass

    @abstractmethod
    def resume(self):
        pass