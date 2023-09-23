# Class for each printer.
class Printer:
    def __init__(self, name, address, status):
        self.name = name
        self.address = address
        self.status = status

    def getStatus(self):
        return self.status
