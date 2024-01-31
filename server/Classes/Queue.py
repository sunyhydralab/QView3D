from collections import deque
class Queue: 
    # Only adding ID to the queue 
    def __init__(self):
        self.__queue = deque() # use Python double-ended queue  
    
    # if no priority add to end of queue. If priority add to front of queue. 
    def addToBack(self, jobid):
        if self.__queue.count(jobid)>0: 
            raise Exception("Job ID already in queue.") 
        self.__queue.append(jobid) # appending on the right is the "front" because popping takes out from right d
    
    def addToFront(self, jobid): 
        if self.__queue.count(jobid)>0: 
            raise Exception("Job ID already in queue.") 
        self.__queue.appendleft(jobid)
    
    def bump(self, up, jobid): # up = boolean. if up = true bump up, else bump down 
        index = list(self.__queue).index(jobid)
        if up==True: 
            self.__queue.remove(jobid)
            self.__queue.insert(index-1, jobid)
        else: 
            self.__queue.remove(jobid)
            self.__queue.insert(index+1, jobid)
            pass 
    
    def deleteJob(self, jobid): 
        if self.__queue.count(jobid)<=0: 
            raise Exception("Job not in queue.") 
        self.__queue.remove(jobid)
    
    def bumpExtreme(self, front, jobid): # bump to back/front of queue 
        if(front == True):
            self.__queue.remove(jobid)
            self.addToFront(jobid)
        else: 
            self.__queue.remove(jobid)
            self.addToBack(jobid) 
            
    def getQueue(self): 
        return self.__queue
    
    def getNext(self): 
        return self.__queue[0]
    
    def getSize(self): 
        return len(self.__queue)
    
    def removeJob(self):
        self.__queue.pop()
    
    

# test = Queue()

# test.addToFront(1)
# test.addToFront(2)
# test.addToFront(3)
# test.addToFront(4)
# test.addToFront(5)
# # test.addToBack(10)
# # test.addToFront(11)
# # test.bumpExtreme(False, 2)
# test.bump(False, 2)

# print(test.getNext())
# print(test.getQueue())