import threading
from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import reconstructor
from Classes.FabricatorConnection import FabricatorConnection
from Classes.Fabricators.Device import Device
from typing_extensions import TextIO
from Classes.Jobs import Job
from Mixins.hasEndingSequence import hasEndingSequence
from config.db import db
from datetime import datetime, timezone
from services.app_service import current_app

class Fabricator(db.Model):
    __tablename__ = "Fabricators"
    dbID = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)
    devicePort = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(100), nullable=True)

    @reconstructor
    def init_on_load(self):
        from Classes.Queue import Queue
        self._status_lock = threading.RLock()
        self._status = 'offline'
        if not hasattr(self, 'queue') or self.queue is None:
            self.queue = Queue()
        if not hasattr(self, 'device'):
            self.device = None
        if not hasattr(self, 'error'):
            self.error = None

    def __init__(self, port=None, name="", consoleLogger=None, fileLogger=None, devicePort=None):
        if devicePort is not None and devicePort.startswith('EMU_'):
            from Classes.Queue import Queue
            self.dbID = None
            self.queue = Queue()
            self._status_lock = threading.RLock()
            self._status = "ready"
            self.hwid = devicePort
            self.description = "Emulated Printer"
            self.name = name if name else "Emulated Printer"
            self.devicePort = devicePort
            self.device = None
            self.date = datetime.now(timezone.utc).astimezone()
            self.error = None
            return

        if port is None:
            return
        assert isinstance(port, ListPortInfo) or isinstance(port, SysFS), f"Invalid port type: {type(port)}"
        assert isinstance(name, str), f"Invalid name type: {type(name)}"
        from Classes.Queue import Queue
        self.dbID = None
        self.queue = Queue()
        self._status_lock = threading.RLock()
        self._status = "configuring"
        self.hwid = port.hwid.split(" LOCATION=")[0]
        self.description = "New Fabricator"
        self.name = name
        self.devicePort = port.device.strip("/").split("/")[-1]
        dbFab = Fabricator.query.filter_by(hwid=self.hwid).first()
        if dbFab is None:
            db.session.add(self)
            db.session.commit()
            self.dbID = self.dbID
        else:
            self.name = dbFab.name
            self.description = dbFab.description
            self.hwid = dbFab.hwid
            self.devicePort = dbFab.devicePort.strip("/").split("/")[-1]
            self.date = dbFab.date
            self.dbID = dbFab.dbID
        self.device = self.createDevice(port, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=True, websocket_connection=next(iter(current_app.emulator_connections.values())) if port.device == current_app.get_emu_ports()[0] else None, name=name)
        if self.description == "New Fabricator": self.description = self.device.getDescription()
        self.error = None
        db.session.commit()

    def __repr__(self):
        return f"Fabricator: {self.name}, description: {self.description}, HWID: {self.hwid}, port: {self.devicePort}, status: {self.status}, logger: {self.device.logger if hasattr(self, 'device') and hasattr(self.device, 'logger') else 'None'}, port open: {self.device.serialConnection.is_open if hasattr(self, 'device') and self.device and self.device.serialConnection else None}, queue: {self.queue}, job: {self.queue[0]}"

    @property
    def status(self):
        with self._status_lock:
            return self._status

    @status.setter
    def status(self, value):
        with self._status_lock:
            self._status = value

    def __to_JSON__(self):
        queue_data = []
        if hasattr(self, 'queue') and self.queue is not None:
            try:
                if hasattr(self.queue, 'convertQueueToJson'):
                    queue_data = self.queue.convertQueueToJson()
                elif isinstance(self.queue, list):
                    queue_data = [job.__to_JSON__() if hasattr(job, '__to_JSON__') else {} for job in self.queue]
            except Exception:
                queue_data = []

        current_job = None
        if hasattr(self, 'queue') and self.queue is not None:
            try:
                if len(self.queue) > 0 and self.queue[0] is not None:
                    current_job = self.queue[0].__to_JSON__() if hasattr(self.queue[0], '__to_JSON__') else None
            except Exception:
                current_job = None

        device_data = None
        if hasattr(self, 'device') and self.device is not None:
            try:
                device_data = self.device.__to_JSON__() if hasattr(self.device, '__to_JSON__') else None
            except Exception:
                device_data = None

        return {
            "name": getattr(self, 'name', 'Unknown'),
            "description": getattr(self, 'description', 'Unknown'),
            "hwid": getattr(self, 'hwid', 'Unknown'),
            "status": getattr(self, 'status', 'offline'),
            "id": getattr(self, 'dbID', None),
            "date": self.date.strftime("%a, %d %b %Y %H:%M:%S") if hasattr(self, 'date') and self.date else None,
            "queue": queue_data,
            "job": current_job,
            "device": device_data,
            "consoles": [[],[],[],[],[]],
            "model": getattr(self, 'model', 'Unknown'),
        }

    @staticmethod
    def getModelFromGcodeCommand(serialPort):
        testName = FabricatorConnection.staticCreateConnection(port=serialPort.device, baudrate=115200, timeout=60)
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
    def staticCreateDevice(serialPort, consoleLogger=None, fileLogger=None, websocket_connection=None):
        assert serialPort is not None, "Serial port is None"
        from Classes.Fabricators.Printers.Ender.EnderPrinter import EnderPrinter
        from Classes.Fabricators.Printers.MakerBot.MakerBotPrinter import MakerBotPrinter
        from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
        if serialPort.vid == PrusaPrinter.VENDORID:
            from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
            from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
            from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
            if serialPort.pid == PrusaMK4.PRODUCTID:
                return PrusaMK4(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
            elif serialPort.pid == PrusaMK4S.PRODUCTID:
                return PrusaMK4S(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
            elif serialPort.pid == PrusaMK3.PRODUCTID:
                return PrusaMK3(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
            else:
                return None
        elif serialPort.vid == EnderPrinter.VENDORID:
            from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
            from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
            model = Fabricator.getModelFromGcodeCommand(serialPort)
            if "Ender-3 Pro" in model:
                return Ender3Pro(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
            elif "Ender-3" in model:
                return Ender3(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
            else:
                return None
        elif serialPort.vid == MakerBotPrinter.VENDORID:
            from Classes.Fabricators.Printers.MakerBot.Replicator2 import Replicator2
            if serialPort.pid == Replicator2.PRODUCTID:
                return Replicator2(100000, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=False, websocket_connection=websocket_connection)
        else:
            return None

    def createDevice(self, serialPort, consoleLogger=None, fileLogger=None, addLogger=False, websocket_connection=None, name=None):
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
                return PrusaMK4(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            elif serialPort.pid == PrusaMK4S.PRODUCTID:
                return PrusaMK4S(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            elif serialPort.pid == PrusaMK3.PRODUCTID:
                return PrusaMK3(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            else:
                return None
        elif serialPort.vid == EnderPrinter.VENDORID:
            from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
            from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
            model = Fabricator.getModelFromGcodeCommand(serialPort)
            if "Ender-3 Pro" in model:
                return Ender3Pro(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            elif "Ender-3" in model:
                return Ender3(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            else:
                return None
        elif serialPort.vid == MakerBotPrinter.VENDORID:
            from Classes.Fabricators.Printers.MakerBot.Replicator2 import Replicator2
            if serialPort.pid == Replicator2.PRODUCTID:
                return Replicator2(self.dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
            else:
                return None
        else:
            return None

    @classmethod
    def queryAll(cls):
        return cls.query.all()

    def begin(self):
        try:
            if not self.device.serialConnection.is_open: assert self.device.connect(), "Failed to connect"
            assert self.device.serialConnection.is_open, "Serial connection is not open"
            assert self.status == "printing", f"Fabricator is not printing, status: {self.status}"
            assert self.queue is not None, "Queue is None"
            assert len(self.queue) > 0, "Queue is empty"
            assert self.queue[0] is not None, "Job is None"
            self.checkValidJob()
            assert self.status != "error", "Invalid job"
            assert self.setStatus("printing"), "Failed to set status to printing"
            self.error = self.device.parseGcode(self.queue[0])
            job_logger = self.queue[0].getLogger()
            self.handleVerdict()
            return True
        except Exception as e:
            self.error = e
            current_app.handle_errors_and_logging(e, self.device.logger, level=50)
            current_app.socketio.emit("error_update", {"fabricator_id": self.dbID, "job_id": self.queue[0].id ,"error": str(e)})
            return False

    def pause(self):
        assert isinstance(self.device, Device), f"Device is not a Device object or subclass: {self.device}, type: {type(self.device)}"
        if not self.device.pauseCMD:
            return current_app.handle_errors_and_logging("Fabricator doesn't support pausing", self)
        if self.status != "printing":
            return current_app.handle_errors_and_logging("Nothing to pause, Fabricator isn't printing", self)
        assert self.device.pause(), "Failed to pause"
        self.setStatus("paused")
        return self.status == self.device.status == "paused"

    def resume(self):
        assert isinstance(self.device, Device), f"Device is not a Device object or subclass: {self.device}, type: {type(self.device)}"
        if not self.device.resumeCMD:
            return current_app.handle_errors_and_logging("Fabricator doesn't support pausing", self)
        if self.status != "paused":
            return current_app.handle_errors_and_logging("Nothing to resume, Fabricator isn't paused", self)
        self.setStatus("printing")
        return self.status == self.device.status == "printing"

    def cancel(self):
        try:
            assert self.queue[0] is not None, "Job is None"
            assert self.device is not None, "Device is None"
            if self.status != "printing" and self.status != "paused":
                return current_app.handle_errors_and_logging("Nothing to cancel, Fabricator isn't printing", self)
            self.setStatus("cancelled")
            return self.status == self.device.status == "cancelled"
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.device.logger)

    def getStatus(self):
        return self.status

    def setStatus(self, newStatus):
        try:
            assert newStatus in ["idle", "printing", "paused", "complete", "error", "cancelled", "misprint", "ready", "offline"], f"Invalid status: {newStatus}"
            assert self.device is not None, "Device is None"
            if self.status == "error" and newStatus != "error":
                self.device.hardReset(newStatus)
            if newStatus == "ready":
                if self.device.serialConnection is None or not self.device.serialConnection.is_open: assert self.device.connect(), "Failed to connect"
            elif newStatus == "offline":
                if self.device.serialConnection is not None and self.device.serialConnection.is_open: assert self.device.disconnect(), "Failed to disconnect"
            self.status = newStatus
            self.device.status = newStatus
            if len(self.queue) > 0:
                if self.queue[0] is not None:
                    self.queue[0].status = newStatus
                    db.session.commit()
            if current_app:
                current_app.socketio.emit("status_update", {"fabricator_id": self.dbID, "status": newStatus})
                can_pause = newStatus == "printing"
                current_app.socketio.emit("can_pause", {"fabricator_id": self.dbID, "canPause": can_pause})
                if len(self.queue) > 0 and self.queue[0] is not None:
                    Job.update_job_status(self.queue[0].id, newStatus)
            else:
                print(f"current app is None, status: {newStatus}")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.device.logger)

    def resetToIdle(self):
        self.setStatus("idle")

    def handleVerdict(self):
        assert self.device.verdict in ["complete", "error", "cancelled", "misprint"], f"Invalid verdict: {self.device.verdict}"
        assert self.queue[0] is not None, "Job is None"
        if self.device.verdict == "complete":
            self.setStatus("complete")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "complete"})
        elif self.device.verdict == "error":
            self.setStatus("error")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "error"})
            from Classes.Issues import Issue
            Issue.create_issue(f"CODE ISSUE: Print Failed: {self.name} - {self.queue[0].file_name_original}", self.error, self.queue[0].id)
            self.getQueue().deleteJob(self.queue[0].id, self.dbID)
            self.device.disconnect()
        elif self.device.verdict == "cancelled":
            if isinstance(self.device, hasEndingSequence): self.device.endSequence()
            else: self.device.home()
            self.setStatus("cancelled")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "cancelled"})
            self.queue.removeJob()
        elif self.device.verdict== "misprint":
            self.setStatus("misprint")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "misprint"})

    def getName(self):
        return self.name

    def setName(self, name):
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
        try:
            assert self.queue[0] is not None, "Job is None"
            assert self.device is not None, "Device is None"
            self.queue[0].saveToFolder()
            settingsDict = getFileConfig(self.queue[0].file_path)
            from Classes.Fabricators.Printers.Printer import Printer
            from Classes.Fabricators.CNCMachines.CNCMachine import CNCMachine
            from Classes.Fabricators.LaserCutters.LaserCutter import LaserCutter
            if isinstance(self.device, Printer):
                if self.device.filamentType is None:
                    self.device.filamentType = settingsDict.get("filament_type", "PLA")
                if self.device.filamentDiameter is None:
                    self.device.filamentDiameter = float(settingsDict.get("filament_diameter", "1.75"))
                if self.device.nozzleDiameter is None:
                    self.device.nozzleDiameter = float(settingsDict.get("nozzle_diameter", "0.4"))

                if "filament_type" in settingsDict and self.device.filamentType != settingsDict["filament_type"]:
                    print(f"WARNING: Filament type mismatch: {self.device.filamentType} != {settingsDict['filament_type']}")
                if "filament_diameter" in settingsDict and self.device.filamentDiameter != float(settingsDict["filament_diameter"]):
                    print(f"WARNING: Filament diameter mismatch: {self.device.filamentDiameter} != {float(settingsDict['filament_diameter'])}")
                if "nozzle_diameter" in settingsDict and self.device.nozzleDiameter != float(settingsDict["nozzle_diameter"]):
                    print(f"WARNING: Nozzle diameter mismatch: {self.device.nozzleDiameter} != {float(settingsDict['nozzle_diameter'])}")
            elif isinstance(self.device, CNCMachine):
                pass
            elif isinstance(self.device, LaserCutter):
                pass
        except AssertionError as e:
            current_app.handle_errors_and_logging(e, self.device.logger)
            self.setStatus("error")
            self.queue.removeJob()
            self.queue[0] = None


def getFileConfig(file):
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
