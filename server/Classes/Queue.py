from collections import deque
from globals import current_app
from Classes.Jobs import Job

class Queue(deque):
    """Represents a queue of jobs, used to manage the order of jobs to be fabricated."""

    def __list__(self):
        my_list = []
        for job in self: my_list.append(job.__to_JSON__())
        return my_list

    def setToInQueue(self): 
        for job in self:
            job.status = "inqueue"

    def addToBack(self, job: Job):
        assert isinstance(job, Job)

        if self.count(job) > 0:
            return False
        self.append(job)
        if current_app:
            current_app.socketio.emit(
                 "queue_update", {"queue": self.convertQueueToJson(), "printerid": job.fabricator_id}
            )
        return True

    def addToFront(self, job: Job) -> bool:
        """
        add new job to the front of the Queue
        :param Job job: the job to add
        :rtype: bool
        """
        assert isinstance(job, Job), f"Job must be an instance of Job: {job} : {type(job)}"
        if self.count(job) > 0:
            return False
        if len(self) >= 1 and self[0].status == "printing":
            self.insert(1, job)
        else:
            self.appendleft(job)
        if current_app:
            current_app.socketio.emit(
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": job.fabricator_id}
            )
        return True

    def bump(self, up, jobid):
        """
        Move a job up or down in the queue.
        :param bool up: True to move the job up, False to move it down
        :param int jobid: The ID of the job to move
        """
        index = next(
            (
                index
                for index, queued_job in enumerate(self)
                if queued_job.id == jobid
            ),
            -1,
        )
        if index == -1:
            print("Job not found in queue.")
            return
        job_to_move = self[index]
        self.remove(job_to_move)
        if up and index > 0:
            self.insert(index - 1, job_to_move)
        elif not up and index < len(self):
            self.insert(index + 1, job_to_move)
        if current_app:
            current_app.socketio.emit(
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": job_to_move.fabricator_id}
            )

    def reorder(self, arr):
        """
        Reorder the queue based on a list of job IDs.
        :param list[int] arr: The list of job IDs to reorder the queue by
        """
        new_queue = deque()
        for jobid in arr:
            for job in self:
                if job.getJobId() == jobid:
                    new_queue.append(job)
                    break
        self.clear()
        self.extend(new_queue)

        if current_app:
            current_app.socketio.emit(
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": self[0].fabricator_id if len(self) > 0 else None}
            )
    
    def deleteJob(self, jobid: int, fabricator_id: int) -> Job | str:
        """
        Delete a job from the queue.
        :param int jobid: job id to delete
        :param int fabricator_id: printer id for frontend.
        :return: the deleted job or a message indicating the job was not found
        :rtype: Job | str
        """
        for job in self:
            if job.getJobId() == jobid:
                deletedjob = job
                self.remove(job)
                current_app.socketio.emit(
                    "queue_update",
                    {"queue": self.convertQueueToJson(), "printerid": fabricator_id},
                )
                return deletedjob
        return "Job not found in queue."

    def convertQueueToJson(self) -> list[dict]:
        """
        Convert the queue to a JSON-serializable format.
        :return: list of job dictionaries
        :rtype: list[dict]
        """
        return [job.__to_JSON__() for job in self if job is not None]

    def bumpExtreme(self, front: bool, jobid: int, fabricator_id: int):
        """
        Move a job to the front or back of the queue.
        :param bool front: True to move the job to the front, False to move it to the back
        :param int jobid: The ID of the job to move
        :param int fabricator_id: The ID of the printer to move the job to
        """
        index = next(
            (
                index
                for index, queued_job in enumerate(self)
                if queued_job.id == jobid
            ),
            -1,
        )
        if index == -1:
            print("Job not found in queue.")
            return
        job_to_move = self[index]
        self.remove(job_to_move)
        if front:
            if len(self) >= 1 and self[0].status == "printing":
                self.insert(1, job_to_move)
            else:
                self.insert(0, job_to_move)
        else:
            self.addToBack(job_to_move)
        if current_app:
            current_app.socketio.emit(
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": fabricator_id}
            )

    def getJob(self, job_to_find) -> Job | None:
        """
        Get a job from the queue. This is used to make sure that a Job is in the queue, after fetching it from the db with a query.
        :param Job job_to_find: The job to find
        :return: a job object if found, None otherwise
        :rtype: Job | None
        """
        for job in self:
            if job.getJobId() == job_to_find.getJobId():
                return job
        return None

    def getJobById(self, job_to_find: int) -> Job | None:
        """
        Get a job from the queue by its ID.
        :param int job_to_find: The ID of the job to find
        :return: a job object if found, None otherwise
        :rtype: Job | None
        """
        for job in self:
            if job.getJobId() == job_to_find:
                return job
        return None

    def jobExists(self, jobid: int) -> bool:
        """
        Check if a job exists in the queue.
        :param int jobid: The ID of the job to check for
        :return: True if the job exists, False otherwise
        :rtype: bool
        """
        for job in self:
            if job.id == jobid:
                return True
        return False

    def getNext(self) -> Job | None:
        """
        Get the next job in the queue.
        :rtype: Job | None
        """
        return self[0] if len(self) > 0 else None

    def removeJob(self) -> Job | None:
        """
        Remove the next job from the queue.
        :return: the removed job or None if the queue is empty
        :rtype Job | None
        """
        if len(self) == 0:
            return None
        self.popleft()
        if current_app:
            current_app.socketio.emit("job_removed", {"queue": self.__list__()})