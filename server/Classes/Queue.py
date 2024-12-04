from collections import deque
from app import current_app

from Classes.Jobs import Job

class Queue(deque):
    def setToInQueue(self): 
        for job in self:
            job.status = "inqueue"

    def addToBack(self, job: Job, printerid):
        assert isinstance(job, Job)

        if self.count(job) > 0:
            return False
        self.append(job)
        if current_app:
            current_app.socketio.emit(
                 "queue_update", {"queue": self.convertQueueToJson(), "printerid": printerid}
            )
        return True

    def addToFront(self, job):
        assert isinstance(job, Job)
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
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": arr[0].fabricator_id if arr else None}
            )
    
    def deleteJob(self, jobid, printerid):
        deletedjob = None
        for job in self:
            if job.getJobId() == jobid:
                deletedjob = job
                self.remove(job)
                current_app.socketio.emit(
                    "queue_update",
                    {"queue": self.convertQueueToJson(), "printerid": printerid},
                )
                return deletedjob
        return "Job not found in queue."

    def convertQueueToJson(self):
        queue = [job.__to_JSON__() for job in self]
        # for job in self:
        #     job_info = {
        #         "id": job.id,
        #         "name": job.name,
        #         "status": job.status,
        #         "date": job.date.strftime('%a, %d %b %Y %H:%M:%S'),
        #         "printerid": job.fabricator_id,
        #         "errorid": job.error_id,
        #         "file_name_original": job.file_name_original,
        #         "progress": job.progress,
        #         "sent_lines": job.sent_lines,
        #         "favorite": job.favorite,
        #         "released": job.released,
        #         "file_pause": job.filePause,
        #         "comments": job.comments,
        #         "extruded": job.extruded,
        #         "td_id": job.td_id,
        #         "time_started": job.time_started,
        #         "printer_name": job.fabricator_name,
        #         "max_layer_height": job.max_layer_height,
        #         "current_layer_height": job.current_layer_height,
        #         "filament": job.filament,
        #     }
        #     queue.append(job_info)
        return queue

    def bumpExtreme(self, front, jobid, printerid):
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
            self.addToBack(job_to_move, printerid)
        if current_app:
            current_app.socketio.emit(
                "queue_update", {"queue": self.convertQueueToJson(), "printerid": printerid}
            )

    def getJob(self, job_to_find):
        for job in self:
            if job.getJobId() == job_to_find.getJobId():
                return job
        return None

    def getJobById(self, job_to_find):
        for job in self:
            if job.getJobId() == job_to_find:
                return job
        return None

    def jobExists(self, jobid):
        for job in self:

            if job.id == jobid:
                return True
        return False

    def getNext(self):
        return self[0] if len(self) > 0 else None

    def removeJob(self):
        self.pop()
        if current_app:
            current_app.socketio.emit("job_removed", {"queue": list(self)})