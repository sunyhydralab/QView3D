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
        # Find the index of the job in the queue with the same job_id as the job_id in the job dictionary.
        # If no such job is found, index will be -1.
        index = next((index for index, queued_job in enumerate(self.__queue) if queued_job.job_id == job['job_id']), -1)
        
        # If index is -1, this means that the job was not found in the queue.
        # In this case, print a message to the console and return from the function.
        if index == -1:
            print("Job not found in queue.")
            return
        
        # Store the job to move in the job_to_move variable.
        # This is done before removing the job from the queue, because once the job is removed, self.__queue[index] is no longer valid.
        job_to_move = self.__queue[index]
        
        # Remove the job to move from the queue.
        self.__queue.remove(job_to_move)
        
        # If up is True and index is greater than 0, this means that the job should be bumped up and it's not already at the front of the queue.
        # In this case, insert the job at index-1, which is the position before its current position.
        if up==True and index > 0: 
            self.__queue.insert(index-1, job_to_move)
        
        # If up is False and index is less than the length of the queue, this means that the job should be bumped down and it's not already at the end of the queue.
        # In this case, insert the job at index+1, which is the position after its current position.
        elif not up and index < len(self.__queue): 
            self.__queue.insert(index+1, job_to_move)
    
    def deleteJob(self, jobid):
        deletedjob = None
        for job in self.__queue:
            if job.getJobId() == jobid:
                deletedjob = job
                self.__queue.remove(job)
                return deletedjob
    
    def bumpExtreme(self, front, job): # bump to back/front of queue 
        index = next((index for index, queued_job in enumerate(self.__queue) if queued_job.job_id == job['job_id']), -1)
        if index == -1:
            print("Job not found in queue.")
            return
        job_to_move = self.__queue[index]
        self.__queue.remove(job_to_move)
        if front == True:
            # If the queue has at least one job, insert at the second position
            # because the first position is a job that is currently being printed,
            # and we don't want to interrupt it.
            # LMK IF THIS IS HOW IT SHOULD WORK
            if len(self.__queue) >= 1:
                self.__queue.insert(1, job_to_move)
            # If the queue is empty, just add the job to the front
            else:
                self.__queue.appendleft(job_to_move)
        else: 
            self.addToBack(job_to_move)
    
    def getJob(self, job_to_find):
        for job in self.__queue:
            if job.getJobId() == job_to_find.getJobId():
                return job
        return None  # Return None if job is not found in the queue
         
    def getQueue(self): 
        return self.__queue
    
    def getNext(self): 
        return self.__queue[0]
    
    def getSize(self): 
        return len(self.__queue)
    
    def removeJob(self):
        self.__queue.pop()

    
    

