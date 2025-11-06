from collections import deque
from threading import Lock, Condition
from services.app_service import current_app
from Classes.Jobs import Job

class Queue(deque):
    """
    Thread-safe queue of jobs for fabrication management.

    Uses threading.Lock for mutual exclusion and threading.Condition for
    event-driven notifications when jobs are added or removed.
    """

    def __init__(self):
        """Initialize thread-safe queue with lock and condition variable."""
        super().__init__()
        self._lock = Lock()  # Protects all queue operations
        self._condition = Condition(self._lock)  # For wait/notify on job changes
        self._version = 0  # Incremented on each modification for change detection

    def __list__(self):
        with self._lock:
            my_list = []
            for job in self: my_list.append(job.__to_JSON__())
            return my_list

    def setToInQueue(self):
        with self._lock:
            for job in self:
                job.status = "inqueue"

    def addToBack(self, job: Job):
        """
        Add a job to the back of the queue (thread-safe).
        Notifies waiting threads that a new job is available.
        """
        assert isinstance(job, Job)

        with self._condition:
            if self.count(job) > 0:
                return False
            self.append(job)
            self._version += 1
            self._condition.notify_all()  # Wake up threads waiting for jobs

            if current_app and hasattr(current_app, 'socketio') and current_app.socketio:
                try:
                    current_app.socketio.emit(
                         "queue_update", {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": job.fabricator_id}
                    )
                except Exception as e:
                    print(f"Warning: Failed to emit queue_update via socketio: {e}")
            return True

    def addToFront(self, job: Job) -> bool:
        """
        Add new job to the front of the queue (thread-safe).
        If first job is printing, inserts at position 1 instead of 0.
        Notifies waiting threads that a new job is available.

        :param Job job: the job to add
        :rtype: bool
        """
        assert isinstance(job, Job), f"Job must be an instance of Job: {job} : {type(job)}"

        with self._condition:
            if self.count(job) > 0:
                return False
            if len(self) >= 1 and self[0].status == "printing":
                self.insert(1, job)
            else:
                self.appendleft(job)

            self._version += 1
            self._condition.notify_all()  # Wake up threads waiting for jobs

            if current_app and hasattr(current_app, 'socketio') and current_app.socketio:
                try:
                    current_app.socketio.emit(
                        "queue_update", {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": job.fabricator_id}
                    )
                except Exception as e:
                    print(f"Warning: Failed to emit queue_update via socketio: {e}")
            return True

    def bump(self, up, jobid):
        """
        Move a job up or down in the queue (thread-safe).
        :param bool up: True to move the job up, False to move it down
        :param int jobid: The ID of the job to move
        """
        with self._lock:
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

            self._version += 1
            self._update_queue_positions_unsafe()

            if current_app and hasattr(current_app, 'socketio') and current_app.socketio:
                try:
                    current_app.socketio.emit(
                        "queue_update", {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": job_to_move.fabricator_id}
                    )
                except Exception as e:
                    print(f"Warning: Failed to emit queue_update via socketio: {e}")

    def reorder(self, arr):
        """
        Reorder the queue based on a list of job IDs (thread-safe).
        Updates queue_position field for persistence across restarts.
        :param list[int] arr: The list of job IDs to reorder the queue by
        """
        with self._lock:
            new_queue = deque()
            for jobid in arr:
                for job in self:
                    if job.getJobId() == jobid:
                        new_queue.append(job)
                        break
            self.clear()
            self.extend(new_queue)
            self._version += 1
            self._update_queue_positions_unsafe()

            if current_app and hasattr(current_app, 'socketio') and current_app.socketio:
                try:
                    current_app.socketio.emit(
                        "queue_update", {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": self[0].fabricator_id if len(self) > 0 else None}
                    )
                except Exception as e:
                    print(f"Warning: Failed to emit queue_update via socketio: {e}")
    
    def deleteJob(self, jobid: int, fabricator_id: int) -> Job | str:
        """
        Delete a job from the queue (thread-safe).
        :param int jobid: job id to delete
        :param int fabricator_id: printer id for frontend.
        :return: the deleted job or a message indicating the job was not found
        :rtype: Job | str
        """
        with self._lock:
            for job in self:
                if job.getJobId() == jobid:
                    deletedjob = job
                    self.remove(job)
                    self._version += 1
                    self._update_queue_positions_unsafe()

                    current_app.socketio.emit(
                        "queue_update",
                        {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": fabricator_id},
                    )
                    return deletedjob
            return "Job not found in queue."

    def convertQueueToJson(self) -> list[dict]:
        """
        Convert the queue to a JSON-serializable format (thread-safe).
        :return: list of job dictionaries
        :rtype: list[dict]
        """
        with self._lock:
            return self.convertQueueToJson_unsafe()

    def convertQueueToJson_unsafe(self) -> list[dict]:
        """
        Convert queue to JSON without acquiring lock (must be called within lock context).
        :return: list of job dictionaries
        :rtype: list[dict]
        """
        return [job.__to_JSON__() for job in self if job is not None]

    def bumpExtreme(self, front: bool, jobid: int, fabricator_id: int):
        """
        Move a job to the front or back of the queue (thread-safe).
        :param bool front: True to move the job to the front, False to move it to the back
        :param int jobid: The ID of the job to move
        :param int fabricator_id: The ID of the printer to move the job to
        """
        with self._lock:
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
                # Note: Don't call addToBack here as it would try to acquire lock again
                self.append(job_to_move)

            self._version += 1
            self._update_queue_positions_unsafe()

            if current_app and hasattr(current_app, 'socketio') and current_app.socketio:
                try:
                    current_app.socketio.emit(
                        "queue_update", {"queue": self.convertQueueToJson_unsafe(), "fabricator_id": fabricator_id}
                    )
                except Exception as e:
                    print(f"Warning: Failed to emit queue_update via socketio: {e}")

    def getJob(self, job_to_find) -> Job | None:
        """
        Get a job from the queue (thread-safe).
        :param Job job_to_find: The job to find
        :return: a job object if found, None otherwise
        :rtype: Job | None
        """
        with self._lock:
            for job in self:
                if job.getJobId() == job_to_find.getJobId():
                    return job
            return None

    def getJobById(self, job_to_find: int) -> Job | None:
        """
        Get a job from the queue by its ID (thread-safe).
        :param int job_to_find: The ID of the job to find
        :return: a job object if found, None otherwise
        :rtype: Job | None
        """
        with self._lock:
            for job in self:
                if job.getJobId() == job_to_find:
                    return job
            return None

    def jobExists(self, jobid: int) -> bool:
        """
        Check if a job exists in the queue (thread-safe).
        :param int jobid: The ID of the job to check for
        :return: True if the job exists, False otherwise
        :rtype: bool
        """
        with self._lock:
            for job in self:
                if job.id == jobid:
                    return True
            return False

    def getNext(self) -> Job | None:
        """
        Get the next job in the queue without removing it (thread-safe).
        :rtype: Job | None
        """
        with self._lock:
            return self[0] if len(self) > 0 else None

    def removeJob(self) -> Job | None:
        """
        Remove and return the next job from the queue (thread-safe).
        :return: the removed job or None if the queue is empty
        :rtype Job | None
        """
        with self._lock:
            if len(self) == 0:
                return None
            removed_job = self.popleft()
            self._version += 1
            self._update_queue_positions_unsafe()
            # Note: Frontend uses queue_update event which is emitted elsewhere
            return removed_job

    def wait_for_job(self, timeout=None) -> Job | None:
        """
        Block until a job is available in the queue (thread-safe, event-driven).
        This replaces polling by using condition variable notifications.

        :param timeout: Optional timeout in seconds. If None, waits indefinitely.
        :return: The next job, or None if timeout occurred
        :rtype: Job | None
        """
        with self._condition:
            while len(self) == 0:
                if not self._condition.wait(timeout):
                    # Timeout occurred
                    return None
            # Job is available
            return self[0] if len(self) > 0 else None

    def _update_queue_positions_unsafe(self):
        """
        Update queue_position field for all jobs in queue for database persistence.
        MUST be called within lock context (unsafe = doesn't acquire lock).
        """
        from config.db import db
        for position, job in enumerate(self):
            if hasattr(job, 'queue_position') and job.queue_position != position:
                job.queue_position = position
                # Mark as dirty in SQLAlchemy session
                if db.session.object_session(job):
                    db.session.add(job)
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error updating queue positions: {e}")
            db.session.rollback()
            raise  # Re-raise to propagate error to caller