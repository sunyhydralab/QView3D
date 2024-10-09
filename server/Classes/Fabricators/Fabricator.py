from flask import current_app
from Classes.Fabricators.Device import Device
from Classes.Queue import Queue
#from models.jobs import Job
from models.db import db
from datetime import datetime, timezone

# class Fabricator(db.Model):
#     dbID: int = db.Column(db.Integer, primary_key=True)
#     description: str = db.Column(db.String(50), nullable=False)
#     hwid: str = db.Column(db.String(150), nullable=False)
#     name: str = db.Column(db.String(50), nullable=False)
#     date: datetime = db.Column(
#         db.DateTime,
#         default=lambda: datetime.now(timezone.utc).astimezone(),
#         nullable=False,
#     )
#     devicePort: str = db.Column(db.String(50), nullable=False)
#     device: Device = None
#     verdict: str = None
#     prevMsg: str = None
#     #job: Job = None
#     queue: Queue = None
#     status: str = None

class Fabricator:
    dbID: int = None
    description: str = None
    hwid: str = None
    name: str = None
    date: datetime = None
    devicePort: None
    device: Device = None
    verdict: str = None
    prevMsg: str = None
    # job: Job = None
    queue: Queue = None
    status: str = None


    def __init__(self, device: Device, name):
        self.device = device
        self.name = name
        self.description = device.getDescription()
        self.hwid = device.getHWID()
        self.devicePort = device.getSerialPort().device
        self.device.connect()
        self.date = datetime.now(timezone.utc).astimezone()
        db.session.add(self)

    @classmethod
    def queryAll(cls) -> list["Fabricator"]:
        #return cls.query.all()
        pass

    # def print(self):
    #     # TODO: implement print method
    #     # TODO: start print
    #     # TODO: implement loop
    #         # TODO: check for errors
    #         # TODO: check for completion
    #         # TODO: check for cancellation
    #         # TODO: update progress
    #         # TODO: update status
    #     # TODO: end print
    #     pass
    #
    # def pausePrint(self):
    #     if not isinstance(self.__device, canPause):
    #         return # TODO: return error message
    #     self.__device.pause()
    #     self.setStatus("paused")
    #     #self.__job.setStatus("paused")
    #
    # def resumePrint(self):
    #     if not isinstance(self.__device, canPause):
    #         return #TODO: return error message
    #     self.__device.resume()
    #     self.setStatus("printing")
    #     #self.__job.setStatus("printing")
    #
    # def cancelPrint(self):
    #     # TODO: implement cancel print
    #     pass
    #
    # def getStatus(self):
    #     return self.__status
    # def setStatus(self, newStatus):
    #     try:
    #         print("SETTING STATUS TO:", newStatus)
    #         if self.__status == "error" and newStatus!= "error":
    #             self.__device.hardReset(newStatus)
    #         else:
    #             self.__status = newStatus
    #
    #         current_app.socketio.emit(
    #             "status_update", {"printer_id": self.id, "status": newStatus}
    #         )
    #     except Exception as e:
    #         print("Error setting status:", e)
    #
    #
    # def handleVerdict(self, verdict: str, job):
    #     if verdict == "complete":
    #         self.__device.disconnect()
    #         #self.sendStatusToJob(job, job.id, "complete")
    #         self.setStatus("complete")
    #         #self.__job.setStatus("complete")
    #     elif verdict == "error":
    #         self.__device.disconnect()
    #         #self.__queue.deleteJob(job.id, self.id)
    #         self.setStatus("error")
    #         #self.sendStatusToJob(job, job.id, "error")
    #         # self.setError("Error")
    #     elif verdict == "cancelled":
    #         if isinstance(self.__device, hasEndingSequence):
    #             self.__device.endSequence()
    #         else:
    #             self.__device.home()
    #         #self.sendStatusToJob(job, job.id, "cancelled")
    #         self.setStatus("cancelled")
    #         #self.__job.setStatus("cancelled")
    #         self.__device.disconnect()
    #     elif verdict== "misprint":
    #         self.setStatus("misprint")
    #         #self.__job.setStatus("misprint")
    #         #self.sendStatusToJob(job, job.id, "cancelled")

    def getName(self):
        return self.name

    def getHwid(self):
        return self.hwid

    def getDescription(self):
        return self.description