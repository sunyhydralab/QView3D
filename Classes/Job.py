import serial
import serial.tools.list_ports
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
        self.status = status  # Status of the job

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

    # Method for X3G/GCODE conversion.
    def printFile(self):
        if self.extension == ".gcode":
            pass
            # send to compatible printer
        elif self.extension == ".x3g":
            pass
            # send to compatible printer
            

# import Classes.Printer as Printer
# import itertools
# class Job: 
#     # Initialize the job with just the file. Then in a form, we can begin to 
#     # set some of the other attributes.
#     # id_obj = 0 # ID increases every time there's a new job 
#     def __init__(self, file, quantity, desiredColor, priority):
#         # Info in database
#         # self.__id = Job.id_obj # every time a new object is instantiated, it gets a new ID. maybe delete and make a pk instead
#         # Job.id_obj += 1
#         self.__file = file
#         # self.__jobName = None # name of job (Ex. Johnny Appleseed)
#         self.__quantity = None # Quantity needed from given file. 
#         self.__desiredColor = None #desired color of print. Can look at color loaded on specific bot. 
        
#         self.__id = None # retrieve from DB. Use to put IDs in queue. 
        
#         self.__printer = Printer() # printer to send job to 
#         self.__printStatus = 1 # waiting, printing, complete, error, cancelled. 1 = waiting. 
        
#         # self.__priority = None # Should be 1 if its a priority job. 0 if add to end, 1 if priority, This # marks the position in the queue. Maybe instead could have a boolean to "print next" or "print last" and then allow users to change it around if necessary?
#         # self.__weight = None # Weight of the print. Will help in the filament calculations. 
        
#     # def setJobName(self, name): # set name of job in initial form (ex. name of person, of project...)
#     #     self.__jobName = name 
    
#     # pull from database
#     # def setQuantity(self, num): # Set # of times you want to print this. Maybe option to send to diff printers if quantitiy > 1? 
#     #     self.__quantity = num
        
#     def setId(self, dbid): # 
#         self.__id = dbid
    
#     def setPrinter(self, printer, multiple): # multiple is a boolean value: if quantity > 1, have the option to send the job to multiple printers. 
#         # If 0, search through registeredBots and choose a printer. Toggle to send to 1 or many printers if quantity > 1. 
#         # Else, 
#         # send to specfied printer. 
#         # self.__printer = Bot()
#         return 

#     def setStatus(self, status):  # waiting, printing, complete, error, cancelled. Integer value: 1 = waiting, 2 = printing, 3 = complete... Returns in get statement 
#         self.__printStatus = status 
        
#     def setPriority(self, priority): # Depends on position in queue. Maybe can be high, middle, end priority. High: top of queue, middle: somewhere in middle, avg: end of queue
#         self.__priority = priority 
     
#     # def setWeight(self, size): # weight of the print 
#     #     self.__weight = size
        
#     # boolean 
#     def setComplete(self, status):
#         self.__isComplete = status 
        
#      # Get methods    
#     def getId(self):
#         return self.__id
    
#     def getJobName(self):
#         return self.__jobName
    
#     def getQuantity(self): 
#         return self.__quantity
    
#     def getStatus(self):
#         status = self.__printStatus
#         if(status==1):
#             return "waiting"
#         elif(status==2):
#             return "printing"
#         elif(status==3):
#             return "complete"
#         elif(status==4):
#             return "error"
#         elif(status==5):
#             return "cancelled"

#     def getPrinter(self):
#         return self.__printer
    
#     def getPriority(self):
#         return self.__priority
    
#     def getWeight(self):
#         return self.__weight
    
#     def getComplete(self):
#         return self.__isComplete
    
    
    