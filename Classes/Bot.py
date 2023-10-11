import Queue 
class Bot:
    
    # Data for one printer. Created using the RegisteredBots class. 
    def __init__(self, id): # initial registration of bot 
        self.__id = id
        # self.__model = model 
        self.__isOnline = False # is online/ offline 
        
        self.__printTime = None # array of print time info: total time, time elapsed, time left 
        
        self.__isPrinting = False # is printing / not printing 
        self.__isReady = False # ready to accept new job. This is done by user who marks printer as ready. 

        self.__errorStatus = None # error code if error 
                
        self.__queue = Queue() # Queue of jobs on singular printer  
        
        self.__colorLoaded = None # color of filament on printer. Updated by user. 
        
    
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
            
    # code to continuously check the status of the bot. 
    def checkOnline(self):
        pass
    
    def getPrintInfo():
        pass
    
    def stopPrint(): 
        pass 
    
    def pausePrint(): 
        pass 
    
    def unpausePrint(): 
        pass
    
    def printJob(self, job):
        pass
    
    def getId(self):
        return self.__id