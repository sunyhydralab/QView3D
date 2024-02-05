from collections import deque
class Queue: 
    # Only adding ID to the queue 
    def __init__(self):
        self.__queue = deque() # use Python double-ended queue  
    
            
    def __iter__(self): # iterate over queue 
        return iter(self.__queue)
    
    # if no priority add to end of queue. If priority add to front of queue. 
    def addToBack(self, job):
        if self.__queue.count(job)>0: 
            raise Exception("Job ID already in queue.") 
        self.__queue.append(job) # appending on the right is the "front" because popping takes out from right d
    
    def addToFront(self, job): 
        if self.__queue.count(job)>0: 
            raise Exception("Job ID already in queue.") 
        self.__queue.appendleft(job)
    
    def bump(self, up, job): # up = boolean. if up = true bump up, else bump down 
        index = list(self.__queue).index(job)
        if up==True: 
            self.__queue.remove(job)
            self.__queue.insert(index-1, job)
        else: 
            self.__queue.remove(job)
            self.__queue.insert(index+1, job)
            pass 
    
    def deleteJob(self, job): 
        if self.__queue.count(job)<=0: 
            raise Exception("Job not in queue.") 
        self.__queue.remove(job)
    
    def bumpExtreme(self, front, job): # bump to back/front of queue 
        if(front == True):
            self.__queue.remove(job)
            self.addToFront(job)
        else: 
            self.__queue.remove(job)
            self.addToBack(job) 
            
    def getQueue(self): 
        return self.__queue
    
    def getNext(self): 
        return self.__queue[0]
    
    def getSize(self): 
        return len(self.__queue)
    
    def removeJob(self):
        self.__queue.pop()

    
    

