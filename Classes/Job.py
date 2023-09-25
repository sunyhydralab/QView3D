# Class for each printer job.
class Job:
    def __init__(self, name, file, quantity, position, printers):
        self.name = name
        self.file = file
        self.quantity = quantity
        self.position = position
        self.printers = printers
        self.status = ""
        # If printer is makerbot
        self.convertFile()
        # else
        self.printFile()

    def convertFile(self):
        pass

    def printFile(self):
        pass
