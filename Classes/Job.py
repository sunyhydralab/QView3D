import serial
from serial.tools import list_ports
import time

# Class for each printer job.
class Job:
    # Constructor for the Job class
    def __init__(self, file, name, quantity, priority, status):
        self.file = file  # The G-code file
        self.name = name  # Name of the job
        self.gcode_lines = self.loadGcode(file)  # List containing the G-code lines
        self.quantity = quantity  # Quantity of the job
        self.priority = priority  # Priority of the job
        self.status = status  # Status of the job. (completed, error, cancelled, printing, in-queue, or failed.)
        self.version = 1 

    # Method to load G-code from a given file.
    def loadGcode(self, file):
        lines = []
        with open(file, "r") as g:
            for line in g:
                line = line.strip()  # Remove whitespace
                if len(line) == 0:  # Do not send blank lines
                    continue
                if ";" in line:  # Remove inline comments
                    line = line.split(";")[
                        0
                    ].strip()  # Remove comments starting with ";"
                if len(line) == 0 or line.startswith(
                    ";"
                ):  # Don't send empty lines and comments
                    continue
                lines.append(line)  # Add the G-code line to the list
        return lines  # Return the list of G-code lines

    # Method to find file type.
    def fileType(self):
        name, ext = os.path.splitext(file)
        self.extension = ext
        
    def setVersion(self, version_update):
        self.version = version_update; 
    
    def getVersion(self): 
        return self.version

    # Method for X3G/GCODE conversion.
    # def printFile(self):
    #     if self.extension == ".gcode":
    #         pass
    #         # send to compatible printer
    #     elif self.extension == ".x3g":
    #         pass
    #         # send to compatible printer
            
    def getFile(self): 
        return self.file