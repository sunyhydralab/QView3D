# Class for each printer job.
class Job:
    def __init__(self, name, file, quantity, position, printers):
        self.name = name
        self.file = file
        self.quantity = quantity
        self.position = position
        self.printers = printers
        self.status = ""
        
        self.extension = ""
        # If printer is makerbot
        # self.convertFile()
        # sets the extension 
        self.fileType() 
        # else
        self.printFile()

    def fileType(self):
        name, ext = os.path.splitext(file)
        self.extension = ext
        
    def printFile(self):
        if(self.extension == ".gcode"):
            # send to compatible printer 
        elif(self.extension == ".x3g"): 
            # send to compatible printer 
