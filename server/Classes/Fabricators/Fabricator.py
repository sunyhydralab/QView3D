import serial
from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy.exc import SQLAlchemyError

from Classes.Fabricators.Device import Device
from Mixins.canPause import canPause
from Mixins.hasEndingSequence import hasEndingSequence
#from Mixins.hasStartupSequence import hasStartupSequence
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


    def __init__(self, port: ListPortInfo | SysFS | None, name: str = "", addToDB: bool = False, consoleLogger=None, fileLogger=None):
        if port is None:
            return
        assert isinstance(port, ListPortInfo) or isinstance(port, SysFS)
        assert isinstance(name, str)

        from Classes.Queue import Queue
        from Classes.Jobs import Job

        self.device: Device = Fabricator.createDevice(port, consoleLogger=consoleLogger, fileLogger=fileLogger)
        self.job: Job | None = None

        self.queue: Queue = Queue()
        self.status: str = "idle"

        self.name: str = name
        self.description = self.device.getDescription()
        self.hwid = self.device.getHWID()
        self.devicePort = self.device.getSerialPort().device

        self.device.connect()
        if addToDB:
            db.session.add(self)
            db.session.commit()

    def __repr__(self):
        return f"Fabricator: {self.name}, description: {self.description}, HWID: {self.hwid}, port: {self.devicePort}, status: {self.status}"
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
        return response


    @staticmethod
    def createDevice(serialPort: ListPortInfo | SysFS | None, consoleLogger=None, fileLogger=None) -> Device | None:
        """creates the correct printer object based on the serial port info"""
        if serialPort is None:
            return None
        from Classes.Fabricators.Printers.Ender.EnderPrinter import EnderPrinter
        from Classes.Fabricators.Printers.MakerBot.MakerBotPrinter import MakerBotPrinter
        from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
        if serialPort.vid == PrusaPrinter.VENDORID:
            from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
            from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
            from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
            if serialPort.pid == PrusaMK4.PRODUCTID:
                return PrusaMK4(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif serialPort.pid == PrusaMK4S.PRODUCTID:
                return PrusaMK4S(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif serialPort.pid == PrusaMK3.PRODUCTID:
                return PrusaMK3(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            else:
                return None
        elif serialPort.vid == EnderPrinter.VENDORID:
            from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
            from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
            model = Fabricator.getModelFromGcodeCommand(serialPort)
            if "Ender-3 Pro" in model:
                return Ender3Pro(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif "Ender-3" in model:
                return Ender3(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            else:
                return None
        elif serialPort.vid == MakerBotPrinter.VENDORID:
            from Classes.Fabricators.Printers.MakerBot.Replicator2 import Replicator2
            if serialPort.pid == Replicator2.PRODUCTID:
                return Replicator2(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
        else:
            #TODO: assume generic printer, do stuff
            return None

    @classmethod
    def queryAll(cls) -> list["Fabricator"]:
        """return all fabricators in the database"""
        fabList = []
        from Classes.Ports import Ports
        for fab in cls.query.all():
            if Ports.getPortByName(fab.devicePort) is not None:
                fabList.append(cls(Ports.getPortByName(fab.devicePort), fab.name))
        return fabList

    @classmethod
    def updateDB(cls):
        """commits all changes to the db"""
        db.session.commit()

    def addToDB(self):
        db.session.add(self)
        db.session.commit()

    def begin(self):
        """starts the fabrication process"""
        assert self.status == "idle"
        assert self.queue is not None
        assert len(self.queue) > 0

        self.job = self.queue.getNext()

        # if isinstance(self.device, hasStartupSequence):
        #     self.device.startupSequence()

        if self.job is None:
            return # TODO: return error message

        assert self.setStatus("printing"), "Failed to set status to printing"
        assert self.device.parseGcode(self.job.file_name_original), f"Failed to parse Gcode, status: {self.status}, verdict: {self.device.verdict}, file: {self.job.file_name_original}" # this is the actual command to read the file and fabricate.
        self.handleVerdict()

    def pause(self):
        """pauses the fabrication process if the fabricator supports it"""
        if not isinstance(self.device, canPause):
            return # TODO: return error message
        if self.status != "printing":
            return # TODO: return error message
        self.setStatus("paused")
        assert isinstance(self.device, Device)
        return self.status == self.device.status == "paused"

    def resume(self):
        """resumes the fabrication process if the fabricator supports it"""
        if not isinstance(self.device, canPause):
            return #TODO: return error message
        if self.status != "paused":
            return #TODO: return error message
        self.setStatus("printing")
        assert isinstance(self.device, Device)
        return self.status == self.device.status == "printing"

    def cancel(self):
        """cancels the fabrication process"""
        try:
            assert self.job is not None
            assert self.device is not None
            if self.status != "printing" and self.status != "paused":
                self.device.logger.error(f"Fabricator isn't in the middle of a job: current status: {self.status}")
                return #TODO: return error message
            self.setStatus("cancelled")
            return self.status == self.device.status == "cancelled"
        except Exception as e:
            if self.device is None:
                print(e)
            else:
                self.device.logger.error("Error cancelling job:")
                self.device.logger.error(e)
            return False

    def getStatus(self):
        return self.status

    def setStatus(self, newStatus):
        try:
            assert newStatus in ["idle", "printing", "paused", "complete", "error", "cancelled", "misprint"]
            assert self.device is not None

            if self.status == "error" and newStatus!= "error":
                self.device.hardReset(newStatus)
            self.status = newStatus
            self.device.status = newStatus
            if self.job is not None:
                self.job.status = newStatus


            # current_app.socketio.emit(
            #     "status_update", {"fabricator_id": self.dbID, "status": newStatus}
            # )
            return True
        except Exception as e:
            if self.device is None:
                print(e)
            else:
                self.device.logger.error("Error setting status:")
                self.device.logger.error(e)
            return False

    def resetToIdle(self):
        #TODO: send message to front end insuring that the print bed is clear and that the job is done
        self.setStatus("idle")

    def handleVerdict(self):
        assert self.device.verdict in ["complete", "error", "cancelled", "misprint"], f"Invalid verdict: {self.device.verdict}"
        assert self.job is not None
        if self.device.verdict == "complete":
            #self.device.disconnect()
            self.setStatus("complete")
            self.queue.removeJob()
            self.job = None
            # todo: reset to idle
        elif self.device.verdict == "error":
            #self.device.disconnect()
            self.setStatus("error")
        elif self.device.verdict == "cancelled":
            if isinstance(self.device, hasEndingSequence): self.device.endSequence()
            else: self.device.home()
            #self.device.disconnect()
            self.setStatus("cancelled")
            self.queue.removeJob()
            self.job = None
            #todo: reset to idle
        elif self.device.verdict== "misprint":
            self.setStatus("misprint")

    def getName(self):
        return self.name

    def setName(self, name: str) -> Response:
        try:
            Fabricator.query.filter_by(hwid=self.hwid).first().name = name
            self.name = name
            db.session.commit()
            return jsonify({"success": True, "message": "Fabricator name successfully updated.", "code": 200})
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to update fabricator name. Database error", "code": 500})

    def getHwid(self):
        return self.hwid

    def getDescription(self):
        return self.description