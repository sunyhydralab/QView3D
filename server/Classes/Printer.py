from flask import current_app
from Classes.Device import Device
from Classes.Queue import Queue
from Interfaces.canPause import canPause
from models.jobs import Job
from models.db import db
from datetime import datetime, timezone
from Interfaces.hasEndingSequence import hasEndingSequence

class Printer(db.Model):
    __dbID: int = db.Column(db.Integer, primary_key=True)
    __description: str = db.Column(db.String(50), nullable=False)
    __hwid: str = db.Column(db.String(150), nullable=False)
    __name: str = db.Column(db.String(50), nullable=False)
    __date: datetime = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).astimezone(),
        nullable=False,
    )
    __devicePort: str = db.Column(db.String(50), nullable=False)
    __device: Device = None
    __verdict: str = None
    __prevMsg: str = None
    __job: Job = None
    __queue: Queue = None
    __status: str = None

    def __init__(self, device: Device, name):
        self.__device = device
        self.__name = name
        self.__description = device.getDescription()
        self.__hwid = device.getHWID()
        self.__devicePort = device.getSerialPort().device
        self.__device.connect()
        db.session.add(self)

    @classmethod
    def queryAll(cls) -> list["Printer"]:
        return cls.query.all()

    def print(self):
        # TODO: implement print method
        # TODO: start print
        # TODO: implement loop
            # TODO: check for errors
            # TODO: check for completion
            # TODO: check for cancellation
            # TODO: update progress
            # TODO: update status
        # TODO: end print
        pass

    def pausePrint(self):
        if not isinstance(self.__device, canPause):
            return # TODO: return error message
        self.__device.pause()
        self.setStatus("paused")
        self.__job.setStatus("paused")

    def resumePrint(self):
        if not isinstance(self.__device, canPause):
            return #TODO: return error message
        self.__device.resume()
        self.setStatus("printing")
        self.__job.setStatus("printing")

    def cancelPrint(self):
        pass

    def getStatus(self):
        return self.__status
    def setStatus(self, newStatus):
        try:
            print("SETTING STATUS TO:", newStatus)
            if self.__status == "error" and newStatus!= "error":
                Printer.hardReset(self.id, newStatus)
            else:
                self.__status = newStatus

            current_app.socketio.emit(
                "status_update", {"printer_id": self.id, "status": newStatus}
            )
        except Exception as e:
            print("Error setting status:", e)


    def handelVerdict(self, verdict: str, job):
        if verdict == "complete":
            self.__device.disconnect()
            #self.sendStatusToJob(job, job.id, "complete")
            self.setStatus("complete")
            self.__job.setStatus("complete")
        elif verdict == "error":
            self.disconnect()
            self.__queue.deleteJob(job.id, self.id)
            self.setStatus("error")
            self.sendStatusToJob(job, job.id, "error")
            # self.setError("Error")
        elif verdict == "cancelled":
            if isinstance(self.__device, hasEndingSequence):
                self.__device.endSequence()
            else:
                self.__device.home()
            #self.sendStatusToJob(job, job.id, "cancelled")
            self.setStatus("cancelled")
            self.__job.setStatus("cancelled")
            self.disconnect()
        elif verdict== "misprint":
            self.setStatus("misprint")
            self.__job.setStatus("misprint")
            #self.sendStatusToJob(job, job.id, "cancelled")

    def getName(self):
        return self.__name

    def getHwid(self):
        return self.__hwid

    def getDescription(self):
        return self.__description