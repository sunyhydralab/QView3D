import os
import re

from flask import jsonify, Response
from sqlalchemy.exc import SQLAlchemyError
from Classes.Fabricators.Device import Device
from Classes.Fabricators.Device_Factory import DeviceFactory
from typing_extensions import TextIO
from Classes.Jobs import Job
from Mixins.hasEndingSequence import hasEndingSequence
from models.config import Config
from models.db import db
from datetime import datetime, timezone
from globals import current_app, root_path, system_device_prefix
from pyvisa.resources.resource import Resource

class Fabricator(db.Model):
    __tablename__ = "Fabricators"
    """Fabricator class for the database. This is used for all io operations with the database, the hardware, and the front end."""
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

    def __init__(self, port: str | Resource | None, name: str = "", consoleLogger: TextIO | None = None, fileLogger: str | None = None):
        """
        Initialize a new Fabricator instance.
        :param str | Resource | None port: the serial port to connect to
        :param str name: the name to show the frontend
        :param TextIO | None consoleLogger: the console to log to
        :param str | None fileLogger: the file path to log to
        """
        if port is None:
            return
        if isinstance(port, Resource): port_string = port.resource_name
        elif isinstance(port, str): port_string = port
        else: raise AssertionError(f"Invalid port type: {type(port)}")
        assert isinstance(name, str), f"Invalid name type: {type(name)}"
        if re.match(system_device_prefix + r"\d+", port_string):
            port_string = f"ASRL{re.sub(system_device_prefix, '', port_string)}::INSTR"
        if current_app.resource_manager.list_opened_resources():
            resource = next((resource for resource in current_app.resource_manager.list_opened_resources() if resource.resource_name == port_string), None)
            if resource: port = resource
            else: port = current_app.resource_manager.open_resource(port_string, baud_rate=115200, open_timeout=5000)
        else: port = current_app.resource_manager.open_resource(port_string, baud_rate=115200, open_timeout=5000)
        from Classes.Queue import Queue
        self.dbID = None  # Initialize dbID
        self.queue: Queue = Queue()
        self.status: str = "configuring"
        self.hwid = port.hwid if hasattr(port, "hwid") else ""
        self.description = "New Fabricator"
        self.name: str = name
        self.devicePort = port.comm_port if hasattr(port, "comm_port") else ""
        dbFab = Fabricator.query.filter_by(hwid=self.hwid).first()
        if dbFab is None:
            db.session.add(self)
            db.session.commit()
            self.dbID = self.dbID  # Set dbID after committing to the database
        else:
            self.name = dbFab.name
            self.description = dbFab.description
            self.hwid = dbFab.hwid
            self.devicePort = dbFab.devicePort.strip("/").split("/")[-1]
            self.date = dbFab.date
            self.dbID = dbFab.dbID
        self.device = DeviceFactory(port, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=True, websocket_connection=next(iter(current_app.emulator_connections.values())) if port.comm_port == current_app.get_emu_ports()[0] else None, dbID=self.dbID, name=name)
        if self.description == "New Fabricator": self.description = self.device.getDescription()
        self.error = None
        db.session.commit()

    def __repr__(self):
        return f"Fabricator: {self.name}, description: {self.description}, HWID: {self.hwid}, port: {self.devicePort}, status: {self.status}, logger: {self.device.logger if hasattr(self, 'device') and hasattr(self.device, 'logger') else 'None'}, port open: {self.device.serialConnection.is_open if hasattr(self, 'device') and self.device and self.device.serialConnection else None}, queue: {self.queue}, job: {self.queue[0]}"

    def __to_JSON__(self) -> dict:
        """
        Converts the Fabricator object to a JSON object that can be sent to the front end
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
            "job": self.queue[0].__to_JSON__() if len(self.queue) > 0 and self.queue[0] is not None else None,
            "device": self.device.__to_JSON__(),
            "consoles": [[],[],[],[],[]],
        }

    @classmethod
    def queryAll(cls) -> list["Fabricator"]:
        """
        Returns all fabricators in the database as a list of the Fabricator objects
        :return: list of Fabricator objects in the DB.
        :rtype: list[Fabricator]
        """
        fabList = []
        from Classes.Ports import Ports
        for fab in cls.query.all():
            if Ports.getPortByName(fab.devicePort) is not None:
                fabList.append(cls(Ports.getPortByName(fab.devicePort), fab.name))
        return fabList

    def begin(self, isVerbose: bool = False) -> bool:
        """
        starts the fabrication process
        :param bool isVerbose: whether to print verbose output
        :rtype: bool
        """
        try:
            if not self.device.serialConnection or not self.device.serialConnection.is_open: assert self.device.connect(), "Failed to connect"
            assert self.status == "printing", f"Fabricator is not printing, status: {self.status}"
            assert self.queue is not None, "Queue is None"
            assert len(self.queue) > 0, "Queue is empty"
            assert self.queue[0] is not None, "Job is None"
            self.checkValidJob()
            assert self.status != "error", "Invalid job"
            # if isinstance(self.device, hasStartupSequence):
            #     self.device.startupSequence()
            assert self.setStatus("printing"), "Failed to set status to printing"
            self.error = self.device.parseGcode(self.queue[0], isVerbose=isVerbose) # this is the actual command to read the file and fabricate.
            self.handleVerdict()
            if isVerbose and self.device.logger is not None: self.device.logger.debug(f"Verdict handled, status: {self.status}")
            return True
        except Exception as e:
            self.error = e
            current_app.socketio.emit("error_update", {"fabricator_id": self.dbID, "job_id": self.queue[0].id ,"error": str(e)})
            return current_app.handle_errors_and_logging(e, self.device.logger, level=50)

    def pause(self) -> bool:
        """
        pauses the fabrication process if the fabricator supports it
        :rtype: bool
        :raises AssertionError: if the device doesn't support pausing, or if the fabricator isn't paused despite being capable of it.
        """
        assert isinstance(self.device,
                          Device), f"Device is not a Device object or subclass: {self.device}, type: {type(self.device)}"
        if not self.device.pauseCMD:
            return current_app.handle_errors_and_logging("Fabricator doesn't support pausing", self)
        if self.status != "printing":
            return current_app.handle_errors_and_logging("Nothing to pause, Fabricator isn't printing", self)
        assert self.device.pause(), "Failed to pause"
        self.setStatus("paused")
        return self.status == self.device.status == "paused"

    def resume(self) -> bool:
        """
        resumes the fabrication process if the fabricator supports it
        :rtype: bool
        :raises AssertionError: if the device doesn't support resuming, or if the fabricator hasn't resumed despite being capable of it.
        """
        assert isinstance(self.device,
                          Device), f"Device is not a Device object or subclass: {self.device}, type: {type(self.device)}"
        if not self.device.resumeCMD:
            return current_app.handle_errors_and_logging("Fabricator doesn't support pausing", self)
        if self.status != "paused":
            return current_app.handle_errors_and_logging("Nothing to resume, Fabricator isn't paused", self)
        self.setStatus("printing")
        return self.status == self.device.status == "printing"

    def cancel(self) -> bool:
        """
        cancels the fabrication process
        :rtype: bool
        :raises AssertionError: if the fabricator isn't printing, or if the fabricator hasn't cancelled despite being capable of it
        """
        try:
            assert self.queue[0] is not None, "Job is None"
            assert self.device is not None, "Device is None"
            if self.status != "printing" and self.status != "paused":
                return current_app.handle_errors_and_logging("Nothing to cancel, Fabricator isn't printing", self)
            self.setStatus("cancelled")
            return self.status == self.device.status == "cancelled"
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.device.logger)

    def getStatus(self) -> str:
        """
        gets the status of the fabricator
        :rtype: str
        """
        return self.status

    def setStatus(self, newStatus: str) -> bool:
        """
        sets the status of the fabricator
        :param str newStatus: new status to set
        :rtype: bool
        """
        try:
            assert newStatus in ["idle", "printing", "paused", "complete", "error", "cancelled", "misprint", "ready", "offline"], f"Invalid status: {newStatus}"
            assert self.device is not None, "Device is None"
            if self.status == "error" and newStatus != "error":
                self.device.hardReset(newStatus)
            # this is a hack to make sure that the serial connection is open before setting the status to ready,
            # this should be a temp fix until the serial connection is handled better
            if newStatus == "ready":
                if  self.device.serialConnection is None or not self.device.serialConnection.is_open: assert self.device.connect(), "Failed to connect"
            elif newStatus == "offline":
                if self.device.serialConnection is not None and self.device.serialConnection.is_open: assert self.device.disconnect(), "Failed to disconnect"
            self.status = newStatus
            self.device.status = newStatus
            if len(self.queue) > 0 and self.queue[0] is not None:
                self.queue[0].status = newStatus
                db.session.commit()
            if current_app:
                current_app.socketio.emit(
                    "status_update", {"fabricator_id": self.dbID, "status": newStatus}
                )
                if self.queue[0] is not None:
                    Job.update_job_status(self.queue[0].id, newStatus)
            else:
                print(f"current app is None, status: {newStatus}")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.device.logger)

    def resetToIdle(self):
        #TODO: send message to front end insuring that the print bed is clear and that the job is done
        self.setStatus("idle")

    def handleVerdict(self):
        """handles the verdict of the device, this is used for handling the completion of a job"""
        assert self.device.verdict in ["complete", "error", "cancelled", "misprint"], f"Invalid verdict: {self.device.verdict}"
        assert self.queue[0] is not None, "Job is None"
        if self.device.verdict == "complete":
            self.setStatus("complete")
        elif self.device.verdict == "error":
            self.setStatus("error")
            # create issue
            from models.issues import Issue
            Issue.create_issue(f"CODE ISSUE: Print Failed: {self.name} - {self.queue[0].file_name_original}", self.error, self.queue[0].id)
            # send log to discord
            if Config['discord_enabled']:
                printFile = self.queue[0].file_name_original.split(".gcode")[0]
                printFile = "-".join(printFile.split("_"))
                logFile = os.path.join(root_path, "logs", self.name, printFile, self.job.date.strftime('%m-%d-%Y_%H-%M-%S'), "no color", "DEBUG.log.gz")
                role_message = '<@&{role_id}>'.format(role_id=Config['discord_issues_role'])
                from Discord_bot import sync_send_discord_file
                sync_send_discord_file(logFile, role_message)
            self.getQueue().deleteJob(self.job.id, self.dbID)
            self.device.disconnect()
        elif self.device.verdict == "cancelled":
            if isinstance(self.device, hasEndingSequence): self.device.endSequence()
            else: self.device.home()
            self.setStatus("cancelled")
            self.queue.removeJob()
            self.queue[0] = None
        elif self.device.verdict== "misprint":
            self.setStatus("misprint")

    def getName(self) -> str:
        """
        gets the name of the fabricator
        :rtype: str
        """
        return self.name

    def setName(self, name: str) -> Response:
        """
        sets the name of the fabricator
        :param str name: new name to set
        :rtype: Response
        """
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
            assert self.queue[0] is not None, "Job is None"
            assert self.device is not None, "Device is None"
            self.queue[0].saveToFolder()
            settingsDict = getFileConfig(self.queue[0].file_path)
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
            current_app.handle_errors_and_logging(e, self.device.logger)
            self.setStatus("error")
            self.queue.removeJob()
            self.queue[0] = None


def getFileConfig(file: str) -> dict:
    """
    Get the config lines from the job file.
    :param str file: the file path to the job file
    :rtype: dict
    """
    with open(file, 'r') as f:
        lines = f.readlines()
    comment_lines = [line.strip().lstrip(';').strip() for line in lines if line.strip().startswith(';') or ':' in line]
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
        equalsDict: dict[str, str] = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in comment_lines if '=' in line}
        colonDict: dict[str, str] = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in comment_lines if ':' in line}
        settingsDict: dict[str, str] = {**equalsDict, **colonDict}
        settingsDict["expected_time"] = str(int(settingsDict["TIME"]) + 120)
        settingsDict["filament_type"] = settingsDict["material_type"]
        settingsDict["filament_diameter"] = settingsDict["material_diameter"]
        settingsDict["nozzle_diameter"] = settingsDict["machine_nozzle_size"]
    else:
        equalsDict = {line.split('=')[0].strip(): line.split('=')[1].strip() for line in comment_lines if '=' in line}
        colonDict = {line.split(':')[0].strip(): line.split(':')[1].strip() for line in comment_lines if ':' in line}
        settingsDict = {**equalsDict, **colonDict}
    return settingsDict
