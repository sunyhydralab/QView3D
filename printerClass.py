# Class for each printer job. 
class Job:

    def __init__(self, name, file, quantity, position, printers):
        self.name = name
        self.file = file
        self.quantity = quantity
        self.position = position
        self.printers = printers
        self.status = ""
        #If printer is makerbot
            self.convertFile()
        #else
        self.printFile()
        

    def convertFile(self):
        
    def printFile(self):
    

# Class for each printer.
class Printer:

    def __init__(self, name, address, status):
        self.name = name
        self.address = address
        self.status = status

    def getStatus(self):
        return self.status
