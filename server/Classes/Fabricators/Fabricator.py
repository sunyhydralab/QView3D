import serial
from flask import current_app, jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy.exc import SQLAlchemyError

from Classes.Fabricators.Device import Device
from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
from Classes.Fabricators.Printers.Ender.EnderPrinter import EnderPrinter
from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Ports import Ports
from Classes.Queue import Queue
from Mixins.canPause import canPause
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasStartupSequence import hasStartupSequence
from models.jobs import Job
from models.db import db
from datetime import datetime, timezone

class Fabricator(db.Model):
    dbID = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).astimezone(),
        nullable=False,
    )
    devicePort = db.Column(db.String(50), nullable=False)


    def __init__(self, port: ListPortInfo | SysFS, name: str = "", addToDB: bool = False):
        assert isinstance(port, ListPortInfo) or isinstance(port, SysFS)
        assert isinstance(name, str)

        self.device: Device = Fabricator.createDevice(port)

        self.verdict: str = ""
        self.prevMsg: str = ""
        self.job: Job | None = None
        self.queue: Queue = Queue()
        self.status: str = "idle"

        self.name: str = name
        self.description = self.device.getDescription()
        self.hwid = self.device.getHWID()
        self.devicePort = self.device.getSerialPort().device
        self.date = datetime.now(timezone.utc).astimezone()

        self.device.connect()
        if addToDB:
            db.session.add(self)
            db.session.commit()

    @staticmethod
    def getModelFromGcodeCommand(serialPort: ListPortInfo | SysFS | None) -> str:
        """returns the model of the printer based on the response to M997"""
        testName = serial.Serial(serialPort.device, 115200, timeout=10)
        testName.write(b"M997\n")
        while True:
            response = testName.readline()
            if b"MACHINE_NAME" in response:
                testName.reset_input_buffer()
                testName.close()
                break
        response = response.decode("utf-8")
        # while testName.readline() != b'echo:Unknown command: "M420 S1"\n':
        #     pass
        return response


    @staticmethod
    def createDevice(serialPort: ListPortInfo | SysFS | None):
        """creates the correct printer object based on the serial port info"""
        if serialPort is None:
            return None
        if serialPort.vid == PrusaPrinter.VENDORID:
            if serialPort.pid == PrusaMK4.PRODUCTID:
                return PrusaMK4(serialPort)
            elif serialPort.pid == PrusaMK4S.PRODUCTID:
                return PrusaMK4S(serialPort)
            elif serialPort.pid == PrusaMK3.PRODUCTID:
                return PrusaMK3(serialPort)
            else:
                return None
        elif serialPort.vid == EnderPrinter.VENDORID:
            model = Fabricator.getModelFromGcodeCommand(serialPort)
            if "Ender-3 Pro" in model:
                return Ender3Pro(serialPort)
            elif "Ender-3" in model:
                return Ender3(serialPort)
            else:
                return None
        else:
            return None

    @classmethod
    def queryAll(cls) -> list["Fabricator"]:
        """return all fabricators in the database"""
        fabList = []
        for fab in cls.query.all():
            fabList.append(cls(Ports.getPortByName(fab.devicePort), fab.name))
        return fabList

    def addToDB(self):
        db.session.add(self)
        db.session.commit()

    def begin(self):
        assert self.status == "idle"
        assert self.queue is not None
        assert len(self.queue) > 0

        self.job = self.queue.getJob(self.id)

        # TODO: test if the file has been sliced for the device of this fabricator
        # if issubclass(self.device, PrusaPrinter):
        #     self.device.sendGcode(f"M862.3 P {self.device.getDescription(self.device).split(' ')[1]}\n".encode("utf-8"), lambda x: x == b'ok\n')

        if issubclass(self.device, hasStartupSequence):
            self.device.startupSequence(self)

        self.job = self.queue.getJob(self.id)
        if self.job is None:
            self.setStatus("idle")

        self.setStatus("printing")
        self.device.parseGcode(self.job.file) # this is the actual command to read the file and fabricate.
        self.handleVerdict(self.verdict, self.job)



    def pause(self):
        if not isinstance(self.device, canPause):
            return # TODO: return error message
        self.device.pause()
        self.setStatus("paused")
        #self.job.setStatus("paused")

    def resume(self):
        if not isinstance(self.device, canPause):
            return #TODO: return error message
        self.device.resume()
        self.setStatus("printing")
        #self.job.setStatus("printing")

    def cancel(self):
        # TODO: implement cancel print
        pass

    def getStatus(self):
        return self.status

    def setStatus(self, newStatus):
        try:
            print("SETTING STATUS TO:", newStatus)
            if self.status == "error" and newStatus!= "error":
                self.device.hardReset(newStatus)
            else:
                self.status = newStatus

            current_app.socketio.emit(
                "status_update", {"printer_id": self.id, "status": newStatus}
            )
        except Exception as e:
            print("Error setting status:", e)


    def handleVerdict(self, verdict: str, job):
        if verdict == "complete":
            self.device.disconnect()
            #self.sendStatusToJob(job, job.id, "complete")
            self.setStatus("complete")
            #self.job.setStatus("complete")
            self.queue.removeJob()
        elif verdict == "error":
            self.device.disconnect()
            #self.queue.deleteJob(job.id, self.id)
            self.setStatus("error")
            #self.sendStatusToJob(job, job.id, "error")
            # self.setError("Error")
        elif verdict == "cancelled":
            if isinstance(self.device, hasEndingSequence):
                self.device.endSequence()
            else:
                self.device.home()
            #self.sendStatusToJob(job, job.id, "cancelled")
            self.setStatus("cancelled")
            #self.job.setStatus("cancelled")
            self.device.disconnect()
        elif verdict== "misprint":
            self.setStatus("misprint")
            #self.job.setStatus("misprint")
            #self.sendStatusToJob(job, job.id, "cancelled")

    def getName(self):
        return self.name

    def setName(self, name: str) -> Response:
        try:
            Fabricator.query.filter_by(hwid=self.hwid).first().name = name
            self.name = name
            db.session.commit()
            return jsonify({"success": True, "message": "Printer name successfully updated.", "code": 200})
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to update printer name. Database error", "code": 500})

    def getHwid(self):
        return self.hwid

    def getDescription(self):
        return self.description