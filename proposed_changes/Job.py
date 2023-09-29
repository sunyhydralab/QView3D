import Bot
import itertools
class Job: 
    # Initialize the job with just the file. Then in a form, we can begin to 
    # set some of the other attributes.
    id_obj = 0 # ID increases every time there's a new job 
    def __init__(self, file):
        self.__id = Job.id_obj # every time a new object is instantiated, it gets a new ID
        Job.id_obj += 1
        self.__file = file
        self.__jobName = None # name of job (Ex. Johnny Appleseed)
        self.__quantity = None # Quantity needed from given file 
        self.__printer = Bot() # printer to send job to 
        self.__printStatus = 1 # waiting, printing, complete, error, cancelled. 1 = waiting. 
        self.__priority = None # Should be 1 if its a priority job. This # marks the position in the queue. Maybe instead could have a boolean to "print next" or "print last" and then allow users to change it around if necessary?
        self.__weight = None # Weight of the print. Will help in the filament calculations. 
        self.__isComplete = False # is job complete? 
        
    def setJobName(self, name): # set name of job in initial form (ex. name of person, of project...)
        self.__jobName = name 
    
    def setQuantity(self, num): # Set # of times you want to print this. Maybe option to send to diff printers if quantitiy > 1? 
        self.__quantity = num
        
    def setPrinter(self, printer, multiple): # multiple is a boolean value: if quantity > 1, have the option to send the job to multiple printers. 
        # If 0, search through registeredBots and choose a printer. Toggle to send to 1 or many printers if quantity > 1. 
        # Else, 
        # send to specfied printer. 
        # self.__printer = Bot()
        return 

    def setStatus(self, status):  # waiting, printing, complete, error, cancelled. Integer value: 1 = waiting, 2 = printing, 3 = complete... Returns in get statement 
        self.__printStatus = status 
        
    def setPriority(self, priority): # Depends on position in queue. Maybe can be high, middle, end priority. High: top of queue, middle: somewhere in middle, avg: end of queue
        self.__priority = priority 
     
    def setWeight(self, size): # weight of the print 
        self.__weight = size
        
    # boolean 
    def setComplete(self, status):
        self.__isComplete = status 
        
     # Get methods    
    def getId(self):
        return self.__id
    
    def getJobName(self):
        return self.__jobName
    
    def getQuantity(self): 
        return self.__quantity
    
    def getStatus(self):
        status = self.__printStatus
        if(status==1):
            return "waiting"
        elif(status==2):
            return "printing"
        elif(status==3):
            return "complete"
        elif(status==4):
            return "error"
        elif(status==5):
            return "cancelled"

    def getPrinter(self):
        return self.__printer
    
    def getPriority(self):
        return self.__priority
    
    def getWeight(self):
        return self.__weight
    
    def getComplete(self):
        return self.__isComplete
    
    
    