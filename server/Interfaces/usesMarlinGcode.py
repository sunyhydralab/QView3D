from abc import ABC


class usesMarlinGcode(ABC):

    @staticmethod
    def home():
        return "G28\n"

    @staticmethod
    def diagnose():
        return "M115\n"