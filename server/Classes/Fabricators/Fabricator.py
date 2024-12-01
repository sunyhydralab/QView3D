import io
from sqlite3 import Blob

import serial
from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy.exc import SQLAlchemyError
from Classes.Fabricators.Device import Device
from typing_extensions import TextIO
from Mixins.hasEndingSequence import hasEndingSequence
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


    def __init__(self, port: ListPortInfo | SysFS | None, name: str = "", consoleLogger=None, fileLogger=None):
        if port is None:
            return
        assert isinstance(port, ListPortInfo) or isinstance(port, SysFS), f"Invalid port type: {type(port)}"
        assert isinstance(name, str), f"Invalid name type: {type(name)}"
        from Classes.Queue import Queue
        from Classes.Jobs import Job

        self.dbID = None  # Initialize dbID
        self.job: Job | None = None
        self.queue: Queue = Queue()
        self.status: str = "configuring"
        self.hwid = port.hwid.split(" LOCATION=")[0]
        self.description = "New Fabricator"
        self.name: str = name
        self.devicePort = port.device
        dbFab = Fabricator.query.filter_by(hwid=self.hwid).first()
        if dbFab is None:
            db.session.add(self)
            db.session.commit()
            self.dbID = self.dbID  # Set dbID after committing to the database
        else:
            self.name = dbFab.name
            self.description = dbFab.description
            self.hwid = dbFab.hwid
            self.devicePort = dbFab.devicePort
            self.date = dbFab.date
            self.dbID = dbFab.dbID

        self.device = self.createDevice(port, consoleLogger=consoleLogger, fileLogger=fileLogger)
        if self.description == "New Fabricator": self.description = self.device.getDescription()
        db.session.commit()

    def __repr__(self):
        return f"Fabricator: {self.name}, description: {self.description}, HWID: {self.hwid}, port: {self.devicePort}, status: {self.status}, port open: {self.device.serialConnection.is_open if (self.device is not None and self.device.serialConnection is not None) else None}"

    def __to_JSON__(self):
        """
        Converts the Fabricator object to a JSON object
        :return: JSON object
        :rtype: dict
        """
        return {
            "name": self.name,
            "description": self.description,
            "hwid": self.hwid,
            "status": self.status,
            "id": self.dbID,
            "date": self.date.strftime("%a, %d %b %Y %H:%M:%S"),
            "queue": self.queue.convertQueueToJson(),
            "job": self.job.__to_JSON__() if self.job is not None else None,
            "device": self.device.__to_JSON__(),
        }

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

    def createDevice(self, serialPort: ListPortInfo | SysFS | None, consoleLogger=None, fileLogger=None):
        """
        creates the correct printer object based on the serial port info
        :param serialPort: the serial port info
        :type serialPort: ListPortInfo | SysFS | None
        :param consoleLogger: the console stream to output to
        :type consoleLogger: TextIO | None
        :param fileLogger: the file path to output file logs to
        :type fileLogger: str | None
        :return: the printer object
        :rtype: Device | None
        """
        if serialPort is None:
            return None
        assert isinstance(self, Fabricator), f"self is not a Fabricator object: {self}"
        assert self.dbID is not None, "dbID is None, so there is no way to add the fabricator to the database"
        from Classes.Fabricators.Printers.Ender.EnderPrinter import EnderPrinter
        from Classes.Fabricators.Printers.MakerBot.MakerBotPrinter import MakerBotPrinter
        from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
        if serialPort.vid == PrusaPrinter.VENDORID:
            from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
            from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
            from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
            if serialPort.pid == PrusaMK4.PRODUCTID:
                return PrusaMK4(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif serialPort.pid == PrusaMK4S.PRODUCTID:
                return PrusaMK4S(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif serialPort.pid == PrusaMK3.PRODUCTID:
                return PrusaMK3(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            else:
                return None
        elif serialPort.vid == EnderPrinter.VENDORID:
            from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
            from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
            model = Fabricator.getModelFromGcodeCommand(serialPort)
            if "Ender-3 Pro" in model:
                return Ender3Pro(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            elif "Ender-3" in model:
                return Ender3(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
            else:
                return None
        elif serialPort.vid == MakerBotPrinter.VENDORID:
            from Classes.Fabricators.Printers.MakerBot.Replicator2 import Replicator2
            if serialPort.pid == Replicator2.PRODUCTID:
                return Replicator2(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
        else:
            #TODO: assume generic printer, do stuff
            return None

    @classmethod
    def queryAll(cls):
        """
        Returns all fabricators in the database as a list of the Fabricator objects
        :return: list of Fabricator objects
        :rtype: list[Fabricator]
        """
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
        """adds the fabricator to the db"""
        db.session.add(self)
        db.session.commit()

    def begin(self, isVerbose: bool = False):
        """
        starts the fabrication process
        :param isVerbose: whether to print verbose output
        :type isVerbose: bool
        :return: whether the fabrication process was successful
        :rtype: bool
        """
        try:
            assert self.status == "ready" or "printing", f"Fabricator is not ready or printing, status: {self.status}"
            assert self.queue is not None, "Queue is None"
            assert len(self.queue) > 0, "Queue is empty"
            self.job = self.queue.getNext()
            assert self.job is not None, "Job is None"
            self.checkValidJob()
            assert self.status != "error", "Invalid job"
            # if isinstance(self.device, hasStartupSequence):
            #     self.device.startupSequence()
            assert self.setStatus("printing"), "Failed to set status to printing"
            assert self.device.parseGcode(self.job, isVerbose=isVerbose), f"Failed to parse Gcode, status: {self.status}, verdict: {self.device.verdict}, file: {self.job.file_name_original}" # this is the actual command to read the file and fabricate.
            if isVerbose: self.device.logger.debug(f"Job complete, verdict: {self.device.verdict}")
            self.handleVerdict()
            if isVerbose: self.device.logger.debug(f"Verdict handled, status: {self.status}")
            return True
        except Exception as e:
            from app import handle_errors_and_logging
            return handle_errors_and_logging(e, self)


    def pause(self):
        """pauses the fabrication process if the fabricator supports it"""
        if not self.device.pauseCMD:
            from app import handle_errors_and_logging
            return handle_errors_and_logging("Fabricator doesn't support pausing", self)
        assert isinstance(self.device, Device), f"Device is not a Device object or subclass: {self.device}"
        if self.status != "printing":
            from app import handle_errors_and_logging
            return handle_errors_and_logging("Nothing to pause, Fabricator isn't printing", self)
        assert isinstance(self.device, Device), f"Device is not a Device object or subclass: {self.device}"
        assert self.device.pause(), "Failed to pause"
        self.setStatus("paused")
        return self.status == self.device.status == "paused"

    def resume(self):
        """resumes the fabrication process if the fabricator supports it"""
        if not self.device.resumeCMD:
            from app import handle_errors_and_logging
            return handle_errors_and_logging("Fabricator doesn't support pausing", self)
        if self.status != "paused":
            from app import handle_errors_and_logging
            return handle_errors_and_logging("Nothing to resume, Fabricator isn't paused", self)
        self.setStatus("printing")
        assert isinstance(self.device, Device), f"Device is not a Device object or subclass: {self.device}"
        return self.status == self.device.status == "printing"

    def cancel(self):
        """cancels the fabrication process"""
        try:
            assert self.job is not None, "Job is None"
            assert self.device is not None, "Device is None"
            if self.status != "printing" and self.status != "paused":
                from app import handle_errors_and_logging
                return handle_errors_and_logging("Nothing to cancel, Fabricator isn't printing", self)
            self.setStatus("cancelled")
            return self.status == self.device.status == "cancelled"
        except Exception as e:
            from app import handle_errors_and_logging
            return handle_errors_and_logging(e, self)

    def getStatus(self):
        return self.status

    def setStatus(self, newStatus):
        try:
            assert newStatus in ["idle", "printing", "paused", "complete", "error", "cancelled", "misprint", "ready", "offline"], f"Invalid status: {newStatus}"
            assert self.device is not None, "Device is None"
            if self.status == "error" and newStatus!= "error":
                self.device.hardReset(newStatus)
            self.status = newStatus
            self.device.status = newStatus
            if self.job is not None:
                self.job.status = newStatus

            from flask import current_app
            if current_app:
                current_app.socketio.emit(
                    "status_update", {"fabricator_id": self.dbID, "status": newStatus}
                )
            else:
                print(f"current app is None, status: {newStatus}")
            return True
        except Exception as e:
            from app import handle_errors_and_logging
            return handle_errors_and_logging(e, self)

    def resetToIdle(self):
        #TODO: send message to front end insuring that the print bed is clear and that the job is done
        self.setStatus("idle")

    def handleVerdict(self):
        assert self.device.verdict in ["complete", "error", "cancelled", "misprint"], f"Invalid verdict: {self.device.verdict}"
        assert self.job is not None, "Job is None"
        if self.device.verdict == "complete":
            self.setStatus("complete")
            self.queue.removeJob()
            self.job = None
        elif self.device.verdict == "error":
            self.setStatus("error")
        elif self.device.verdict == "cancelled":
            if isinstance(self.device, hasEndingSequence): self.device.endSequence()
            else: self.device.home()
            self.setStatus("cancelled")
            self.queue.removeJob()
            self.job = None
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

    def getSerialPort(self):
        if self.device is None:
            return None
        return self.device.getSerialPort()

    def getQueue(self):
        return self.queue

    def checkValidJob(self):
        """checks if the job is valid for the fabricator"""
        try:
            assert self.job is not None, "Job is None"
            assert self.device is not None, "Device is None"
            self.job.saveToFolder()
            settingsDict = getFileConfig(self.job.file_path)
            from Classes.Fabricators.Printers.Printer import Printer
            from Classes.Fabricators.CNCMachines.CNCMachine import CNCMachine
            from Classes.Fabricators.LaserCutters.LaserCutter import LaserCutter
            if isinstance(self.device, Printer):
                if self.device.filamentType is None: self.device.filamentType = settingsDict["filament_type"]
                if self.device.filamentDiameter is None: self.device.filamentDiameter = float(settingsDict["filament_diameter"])
                if self.device.nozzleDiameter is None: self.device.nozzleDiameter = float(settingsDict["nozzle_diameter"])
                assert self.device.filamentType == settingsDict["filament_type"], f"Filament type mismatch: {self.device.filamentType} != {settingsDict['filament_type']}"
                assert self.device.filamentDiameter == float(settingsDict["filament_diameter"]), f"Filament diameter mismatch: {self.device.filamentDiameter} != {float(settingsDict['filament_diameter'])}, subtraction test: {self.device.nozzleDiameter - float(settingsDict['nozzle_diameter'])} != 0"
                assert self.device.nozzleDiameter == float(settingsDict["nozzle_diameter"]), f"Nozzle diameter mismatch: {self.device.nozzleDiameter} != {float(settingsDict['nozzle_diameter'])}, subtraction test: {self.device.nozzleDiameter - float(settingsDict['nozzle_diameter'])} != 0.0"
            elif isinstance(self.device, CNCMachine):
                # if self.device.bitDiameter is not None and self.device.bitDiameter != float(settingsDict["bit_diameter"]):
                #     return False
                pass
            elif isinstance(self.device, LaserCutter):
                # if self.device.laserPower is not None and self.device.laserPower != int(settingsDict["laser_power"]):
                #     return False
                pass
        except AssertionError as e:
            self.device.logger.error(f"Invalid job: {e}")
            self.setStatus("error")
            self.queue.removeJob()
            self.job = None


def getFileConfig(file):
    """Get the config lines from the job file."""
    with open(file, 'r') as f:
        lines = f.readlines()
    comment_lines = [line.lstrip(';').strip() for line in lines if line.startswith(';') or ':' in line]
    if len(comment_lines) > 0 and "prusaslicer" in comment_lines[0].lower():
        settingsDict = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in comment_lines if '=' in line}
        import re
        days, hours, minutes, seconds = 0, 0, 0, 0
        timeList = re.findall(r"\d+", settingsDict["estimated printing time (normal mode)"])
        if len(timeList) == 1:
            seconds = map(int, timeList)
        elif len(timeList) == 2:
            minutes, seconds = map(int, timeList)
        elif len(timeList) == 3:
            hours, minutes, seconds = map(int, timeList)
        elif len(timeList) == 4:
            days, hours, minutes, seconds = map(int, timeList)
        settingsDict["expected_time"] = str(days * 86400 + hours * 3600 + (minutes + 2) * 60 + seconds)
    elif len(comment_lines) >= 12 and "cura" in comment_lines[11].lower():
        equalsDict = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in comment_lines if '=' in line}
        colonDict = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in comment_lines if ':' in line}
        settingsDict = {**equalsDict, **colonDict}
        settingsDict["expected_time"] = str(int(settingsDict["TIME"]) + 120)
        settingsDict["filament_type"] = settingsDict["material_type"]
        settingsDict["filament_diameter"] = settingsDict["material_diameter"]
        settingsDict["nozzle_diameter"] = settingsDict["machine_nozzle_size"]
    else:
        equalsDict = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in comment_lines if '=' in line}
        colonDict = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in comment_lines if ':' in line}
        settingsDict = {**equalsDict, **colonDict}
    return settingsDict
