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
    """
    Database model and controller for digital fabrication devices (3D printers, CNC machines, laser cutters).

    Fabricator acts as the bridge between:
    - Database persistence (SQLAlchemy model with hwid, name, port info)
    - Physical device communication (Device instance with serial connection)
    - Job queue management (Queue instance holding pending jobs)
    - Application state (status tracking with thread-safe locking)

    The Fabricator class is responsible for:
    - Registering devices in the database by hardware ID (hwid)
    - Creating appropriate Device subclass instances (Printer, CNC, LaserCutter)
    - Managing device lifecycle (connect, disconnect, status changes)
    - Coordinating job execution via the queue
    - Providing REST API endpoints for device control

    Database Columns:
        dbID (int): Primary key, unique identifier for each fabricator
        description (str): Human-readable description (e.g., "Original Prusa MK4S")
        hwid (str): Hardware ID from USB (e.g., "USB VID:PID=2C99:001A SER=...")
        name (str): User-assigned friendly name for the device
        date (datetime): Registration timestamp
        devicePort (str): Serial port name (e.g., "cu.usbmodem212301")
        model (str): Device model identifier (optional)

    Runtime Attributes (not persisted):
        device (Device): Instance of Printer/CNC/LaserCutter for communication
        queue (Queue): Job queue for this fabricator
        status (str): Current state (offline, ready, printing, paused, error, etc.)
        error (str): Last error message if status is 'error'

    Status Values:
        - offline: Device not connected or not responding
        - configuring: Device is being initialized
        - ready: Device connected and idle, ready for jobs
        - printing: Actively executing a print job
        - paused: Print job paused by user
        - cancelled: Print job cancelled by user
        - complete: Print job finished successfully
        - error: Error occurred during operation
        - awaiting_user_confirmation: Print finished, waiting for user to confirm completion

    Methods:
        __init__(port, name, ...): Initialize new fabricator or load from database
        init_on_load(): Reconstruct runtime attributes when loaded from database
        createDevice(port, ...): Factory method to create appropriate Device subclass
        connect(): Establish serial connection to device
        disconnect(): Close serial connection
        startPrint(job): Begin executing a print job
        pausePrint(): Pause current print job
        resumePrint(): Resume paused print job
        cancelPrint(): Cancel current print job
    """

    __tablename__ = "Fabricators"

    # Database columns (persisted)
    dbID = db.Column(db.Integer, primary_key=True)  # Unique database ID
    description = db.Column(db.String(50), nullable=False)  # Device description
    hwid = db.Column(db.String(150), nullable=False)  # Hardware ID (USB VID:PID:SER)
    name = db.Column(db.String(50), nullable=False)  # User-friendly name
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)  # Registration date
    devicePort = db.Column(db.String(50), nullable=False)  # Serial port name
    model = db.Column(db.String(100), nullable=True)  # Device model

    @reconstructor
    def init_on_load(self):
        """
        Reconstruct runtime attributes when Fabricator is loaded from database.

        Called automatically by SQLAlchemy after querying a Fabricator from the database.
        Initializes non-persistent attributes like queue, device, status, and locks.

        This ensures that fabricators loaded from the database have the same runtime
        state as freshly created ones.
        """
        from Classes.Queue import Queue
        # Thread-safe status management
        self._status_lock = threading.RLock()
        self._status = 'offline'  # Default to offline when loaded from DB
        # Initialize job queue
        if not hasattr(self, 'queue') or self.queue is None:
            self.queue = Queue()
        # Initialize device reference (will be set during connection)
        if not hasattr(self, 'device'):
            self.device = None
        # Initialize error tracking
        if not hasattr(self, 'error'):
            self.error = None

    def __init__(self, port=None, name="", consoleLogger=None, fileLogger=None, devicePort=None):
        """
        Initialize a new Fabricator instance or create emulated fabricator.

        This constructor handles three scenarios:
        1. Emulated fabricator (devicePort starts with 'EMU_')
        2. Real fabricator from serial port (checks database for existing entry by hwid)
        3. No initialization (port=None, used for database queries)

        :param ListPortInfo | SysFS port: Serial port object for the device
        :param str name: User-assigned friendly name
        :param Logger consoleLogger: Optional console logger
        :param Logger fileLogger: Optional file logger
        :param str devicePort: Optional port override for emulator (starts with 'EMU_')

        Behavior:
            - If hwid exists in database: Load existing fabricator data
            - If hwid is new: Create new database entry
            - Automatically creates appropriate Device subclass (Printer/CNC/LaserCutter)
            - Initializes job queue and thread-safe status management
        """
        # ===== SCENARIO 1: Emulated Fabricator =====
        if devicePort is not None and devicePort.startswith('EMU_'):
            from Classes.Queue import Queue
            self.dbID = None  # Emulators are not persisted to database
            self.queue = Queue()
            self._status_lock = threading.RLock()
            self._status = "ready"
            self.hwid = devicePort  # Use devicePort as hwid for emulators
            self.description = "Emulated Printer"
            self.name = name if name else "Emulated Printer"
            self.devicePort = devicePort
            self.device = None  # Device created later via WebSocket connection
            self.date = datetime.now(timezone.utc).astimezone()
            self.error = None
            return

        # ===== SCENARIO 2: Database Query (no initialization) =====
        if port is None:
            return  # Used when querying fabricators from database

        # ===== SCENARIO 3: Real Fabricator from Serial Port =====
        assert isinstance(port, ListPortInfo) or isinstance(port, SysFS), f"Invalid port type: {type(port)}"
        assert isinstance(name, str), f"Invalid name type: {type(name)}"

        from Classes.Queue import Queue
        self.dbID = None
        self.queue = Queue()
        self._status_lock = threading.RLock()
        self._status = "configuring"  # Set to configuring during initialization

        # Extract hardware ID and port info from serial port object
        self.hwid = port.hwid.split(" LOCATION=")[0]  # Remove LOCATION suffix
        self.description = "New Fabricator"  # Temporary, updated after device creation
        self.name = name
        self.devicePort = port.device.strip("/").split("/")[-1]  # Extract port name

        # Check if this fabricator already exists in database (by hwid)
        dbFab = Fabricator.query.filter_by(hwid=self.hwid).first()
        if dbFab is None:
            # New fabricator: Add to database
            db.session.add(self)
            db.session.commit()
            self.dbID = self.dbID
        else:
            # Existing fabricator: Load data from database
            self.name = dbFab.name
            self.description = dbFab.description
            self.hwid = dbFab.hwid
            self.devicePort = dbFab.devicePort.strip("/").split("/")[-1]
            self.date = dbFab.date
            self.dbID = dbFab.dbID

        # Create appropriate Device subclass (Printer, CNC, LaserCutter)
        self.device = self.createDevice(
            port,
            consoleLogger=consoleLogger,
            fileLogger=fileLogger,
            addLogger=True,
            websocket_connection=next(iter(current_app.emulator_connections.values())) if port.device == current_app.get_emu_ports()[0] else None,
            name=name
        )

        # Update description with device-specific info if not already set
        if self.description == "New Fabricator":
            self.description = self.device.getDescription()

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
            # Verify device exists
            if self.device is None:
                raise Exception(f"Fabricator {self.name} (ID: {self.dbID}) has no device initialized. Cannot start print.")

            # Verify serial connection exists
            if not hasattr(self.device, 'serialConnection') or self.device.serialConnection is None:
                raise Exception(f"Fabricator {self.name} has no serial connection. Device may not be connected.")

            # Connect if not open
            if not self.device.serialConnection.is_open:
                assert self.device.connect(), "Failed to connect to device"

            assert self.device.serialConnection.is_open, "Serial connection is not open after connection attempt"
            assert self.status == "printing", f"Fabricator is not printing, status: {self.status}"
            assert self.queue is not None, "Queue is None"
            assert len(self.queue) > 0, "Queue is empty"
            assert self.queue[0] is not None, "Job is None"
            self.checkValidJob()
            assert self.status != "error", "Invalid job"
            assert self.setStatus("printing"), "Failed to set status to printing"

            # Execute print job (blocking call)
            parse_success = self.device.parseGcode(self.queue[0])
            job_logger = self.queue[0].getLogger()

            # Process verdict and update job status
            self.handleVerdict()

            # Return success only if verdict is "complete"
            return self.device.verdict == "complete"
        except Exception as e:
            self.error = e
            error_msg = str(e)
            print(f"[Fabricator] Error in begin() for {self.name}: {error_msg}")
            current_app.handle_errors_and_logging(e, getattr(self.device, 'logger', None) if self.device else None, level=50)

            # Auto-create issue for print start failures with full details
            job = self.queue[0] if self.queue and len(self.queue) > 0 else None
            if job:
                from Classes.Issues import Issue
                issue = Issue.create_issue(
                    title=f"Print Start Failed: {job.file_name_original}",
                    description=f"Printer: {self.name}\nJob: {job.file_name_original} (ID: {job.id})\nError: {error_msg}",
                    severity="high",
                    category="job",
                    job_id=job.id,
                    fabricator_id=self.dbID
                )
                print(f"[Fabricator] Job {job.id} failed to start on {self.name}. Issue #{issue.get('issue_id') if issue else 'N/A'} created")
                current_app.socketio.emit("error_update", {"fabricator_id": self.dbID, "job_id": job.id, "error": error_msg})
            else:
                current_app.socketio.emit("error_update", {"fabricator_id": self.dbID, "job_id": None, "error": error_msg})

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
            return current_app.handle_errors_and_logging(e, getattr(self.device, 'logger', None) if self.device else None)

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
            return current_app.handle_errors_and_logging(e, getattr(self.device, 'logger', None) if self.device else None)

    def resetToIdle(self):
        self.setStatus("idle")

    def handleVerdict(self):
        assert self.device.verdict in ["complete", "error", "cancelled", "misprint"], f"Invalid verdict: {self.device.verdict}"
        assert self.queue[0] is not None, "Job is None"
        job = self.queue[0]

        if self.device.verdict == "complete":
            self.setStatus("complete")
            # Update job status to complete in database
            from Classes.Jobs import Job as JobClass
            JobClass.update_job_status(job.id, "complete")
            print(f"[Fabricator] Job {job.id} marked as complete")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "complete"})
                current_app.socketio.emit("job_completed", {"job_id": job.id, "fabricator_id": self.dbID})
        elif self.device.verdict == "error":
            self.setStatus("error")
            # Update job status to error in database
            from Classes.Jobs import Job as JobClass
            JobClass.update_job_status(job.id, "error")
            # Auto-create issue from error with full details
            from Classes.Issues import Issue
            error_msg = str(self.error) if self.error else "Unknown print error"
            issue = Issue.create_issue(
                title=f"Print Failed: {job.file_name_original}",
                description=f"Printer: {self.name}\nJob: {job.file_name_original} (ID: {job.id})\nError: {error_msg}",
                severity="high",
                category="job",
                job_id=job.id,
                fabricator_id=self.dbID
            )
            print(f"[Fabricator] Job {job.id} failed on {self.name}. Issue #{issue.get('issue_id') if issue else 'N/A'} created")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "error"})
                current_app.socketio.emit("job_error", {"job_id": job.id, "fabricator_id": self.dbID, "error": error_msg})
            self.getQueue().deleteJob(job.id, self.dbID)
            self.device.disconnect()
        elif self.device.verdict == "cancelled":
            # Update job status to cancelled in database
            from Classes.Jobs import Job as JobClass
            JobClass.update_job_status(job.id, "cancelled")
            print(f"[Fabricator] Job {job.id} cancelled by user")
            if isinstance(self.device, hasEndingSequence):
                self.device.endSequence()
            else:
                self.device.home()
            self.setStatus("cancelled")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "cancelled"})
                current_app.socketio.emit("job_cancelled", {"job_id": job.id, "fabricator_id": self.dbID})
            self.queue.removeJob()
        elif self.device.verdict== "misprint":
            # Update job status to error (misprint is a type of error)
            from Classes.Jobs import Job as JobClass
            JobClass.update_job_status(job.id, "error")
            # Auto-create issue for misprint with full details
            from Classes.Issues import Issue
            issue = Issue.create_issue(
                title=f"Misprint: {job.file_name_original}",
                description=f"Printer: {self.name}\nJob: {job.file_name_original} (ID: {job.id})\nIssue: Print quality problem detected",
                severity="medium",
                category="job",
                job_id=job.id,
                fabricator_id=self.dbID
            )
            print(f"[Fabricator] Job {job.id} marked as misprint on {self.name}. Issue #{issue.get('issue_id') if issue else 'N/A'} created")
            self.setStatus("misprint")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": self.dbID, "status": "misprint"})
                current_app.socketio.emit("job_error", {"job_id": job.id, "fabricator_id": self.dbID, "error": "Misprint detected"})

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
            current_app.handle_errors_and_logging(e, getattr(self.device, 'logger', None) if self.device else None)
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
