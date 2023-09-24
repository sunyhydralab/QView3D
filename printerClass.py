# Class for each printer.
class Printer:
    def __init__(self, name, address, status):
        self.__name = name
        self.__address = address
        self.__status = status

    def get_status(self):
        return self.__status
