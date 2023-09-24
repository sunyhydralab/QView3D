# Class for each printer.
class Printer:
    def __init__(self, name, address, status):
        self.__name = name
        self.__address = address
        self.__status = status
        # Either a filament ID or a filament object that keeps track of filament left on roll
        self.__filament

    def get_status(self):
        return self.__status
