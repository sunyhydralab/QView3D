class Queue:
    def __init__(self):
        self.__queue = []

    def add(self, item):
        self.__queue.append(item)

    def remove(self):
        return self.__queue.pop(0)

    def isEmpty(self):
        return len(self.__queue) == 0

    def peek(self):
        return self.__queue[0]

    def __repr__(self):
        return str(self.__queue)


# from collections import deque
# class Queue: 
#     # Only adding ID to the queue 
#     def __init__(self):
#         self.__queue = deque() # use Python double ended queue  
    
#     # if no priority add to end of queue. If priority add to front of queue. 
#     def addToFront(self, jobid): 
#         self.__queue.append(jobid) # appending on the right is the "front" because popping takes out from right 
    
#     def addToBack(self, jobid): 
#         self.__queue.appendleft(jobid)
    
#     def bump(self, up, job): # up = boolean. if up = true bump up, else bump down 
#         pass
    
#     def bumpExtreme(self, front, jobid): # bump to back/front of queue 
#         if(front == True):
#             self.addToFront(self, jobid)
#         else: 
#             self.addToBack(self, jobid) 
    
#     def printJob(self):
#         pass 
    