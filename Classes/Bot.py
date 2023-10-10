import Queue 
class Bot:
    
    # Data for one printer. Created using the RegisteredBots class. 
    def __init__(self, number, model): # initial registration of bot 
        self.__number = number 
        self.__model = model 
        
        self.__isOnline = False # is online/ offline 
                
        self.__isPrinting = False # is printing / not printing 
        self.__donePrinting = False # is it done printing? This is determined by some type of event listener. 
        self.__isReady = False # ready to accept new job. This is done by user who marks printer as ready. 

        self.__errorStatus = None # error code if error 
                
        self.__queue = Queue() # Queue of jobs on singular printer  
        
        self.__colorLoaded = None # color of filament on printer. Updated by user. 
        
        # Maybe too complicated. May delete later. 
        # self.__filamentRemaining = None # amount of filament left. Might be complicated though bc each printer may print at a different rate / errors will affect this value.
        
    # def setOnline(self, status): # True if printer goes online, False if printer goes offline. 
    #     # this is determined by some sort of event listener. 
    #     self.__isOnline = status 
    
    def setError(self, status): # True if there is an error, False if no error. Event listener. 
        if(status == True):
            self.__isReady = False # not ready to print if theres an error 
        self.__isError = status 
    
    def setErrorCode(self, status): # set the error message / code from printer. Event listener. 
        self.__error = status 
    
    def startPrinting(self): # set to printing if printing. Event listener. 
        self.__donePrinting = False # say done Printing is false 
        
    def setReady(self, status): # status is Ready if online and can accept new print. 
        self.__isReady = status 
    
    def addToQueue(self, job): # Add job object to queue 
       # self.__queue.add(job, job.getPriority())
        pass 

    def fetchJob(self):
        if(self.__isReady == True and self.__isOnline == True and self.__isError == False): # if no errors and its ready and online, 
            job = self.__queue.next() # print next job 
            self.printJob(job)
            
    def printJob(self, job):
        pass
    
    def checkAmount(self, job):
        weight = job.getWeight()
        # calculation to update the filament amount / if there will be enough 
        
    
    # code to continuously check the status of the bot. 
    def checkOnline(self):
        pass