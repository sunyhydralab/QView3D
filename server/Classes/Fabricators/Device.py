import os.path
import sys
from abc import ABC
from time import sleep
from globals import current_app, tabs
from Classes.Jobs import Job
from Classes.Vector3 import Vector3
from Classes.Loggers.Logger import Logger
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import checkXYZ
from Classes.FabricatorConnection import SocketConnection, FabricatorConnection
from pyvisa.resources.resource import Resource

class Device(ABC):
    # static variables
    MODEL: str | None = None
    VENDORID: int | None = None
    PRODUCTID: int | None = None
    DESCRIPTION: str | None = None
    MAXFEEDRATE: int | None = None
    serialConnection: SocketConnection | Resource | None = None
    homePosition: Vector3 | None = None

    homeCMD: bytes | None= b"G28\n"
    cancelCMD: bytes | None = None
    keepAliveCMD: bytes | None = None
    doNotKeepAliveCMD: bytes | None = None
    statusCMD: bytes | None = None
    getLocationCMD: bytes | None = None
    pauseCMD: bytes | None = None
    resumeCMD: bytes | None = None
    getMachineNameCMD: bytes | None = None

    callablesHashtable = {
        "G28": [checkXYZ],  # Home
    }

    def __init__(self, dbID: int, serialPort: Resource, consoleLogger=sys.stdout, fileLogger=None, websocket_connection=None, addLogger: bool =False, name: str = None):
        self.name = name if name else self.DESCRIPTION
        self.dbID: int = dbID
        self.serialPort: str | None = serialPort.comm_port
        self.serialID: str | None = serialPort.serial_number
        self.logger = Logger(self.name, port=self.serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, loggingLevel=Logger.DEBUG, consoleLevel=Logger.ERROR) if addLogger else None
        self.status = "idle"
        self.verdict = ""
        self.websocket_connection = websocket_connection
        if self.serialPort:
            self.serialConnection = FabricatorConnection.staticCreateConnection(port=self.serialPort, websocket_connections=self.websocket_connection, fabricator_id=str(self.dbID))

    def __repr__(self):
        return f"port: {self.serialPort}, status: {self.status}, websocket_connection: {self.websocket_connection if self.websocket_connection else 'None'}"

    def __to_JSON__(self):
        return {
            "MODEL": self.MODEL,
            "VENDORID": self.VENDORID,
            "PRODUCTID": self.PRODUCTID,
            "DESCRIPTION": self.DESCRIPTION,
            "MAXFEEDRATE": self.MAXFEEDRATE,
            "serialConnection": {
                "port": self.serialConnection.comm_port,
                "baudrate": self.serialConnection.baud_rate,
                "timeout": self.serialConnection.timeout,
                "is_open": self.serialConnection.is_open,
            } if self.serialConnection else None,
            "homePosition": self.homePosition.__to_JSON__() if self.homePosition else None,
            "dbID": self.dbID,
            "serialPort": self.serialPort if self.serialPort else None,
            "serialID": self.serialID,
            "status": self.status,
            "verdict": self.verdict
        }

    def connect(self) -> bool:
        """Connect to the hardware using the serial port."""
        try:
            assert self.serialPort is not None, "Serial port is not set"
            assert self.serialPort != "", "Serial port device is empty"
            if self.serialConnection is None or not self.serialConnection.is_open:
                print(f"{tabs(tab_change=1)}creating connection to {self.serialPort}...", end="")
                self.serialConnection = FabricatorConnection.staticCreateConnection(port=self.serialPort, baudrate=115200, timeout=60, websocket_connections=self.websocket_connection, fabricator_id=str(self.dbID))
            if self.serialConnection.is_open:
                print(f"{tabs(tab_change=1)}{self.serialPort} is open, resetting input buffer...", end="")
                self.serialConnection.reset_input_buffer()
            print(" Done")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def disconnect(self) -> bool:
        """Disconnect from the hardware by closing the serial connection."""
        try:
            if self.serialConnection and self.serialConnection.is_open:
                self.serialConnection.close()
                self.serialConnection = None
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def home(self, isVerbose: bool = False):
        """
        Home the device.
        :param isVerbose: Whether to log the command.
        :type isVerbose: bool
        :return: True if the device is homed, else False
        :rtype: bool
        """
        try:
            assert isinstance(isVerbose, bool)
            assert isinstance(self, Device)
            self.sendGcode(self.homeCMD, isVerbose=isVerbose)
            assert self.getHomePosition() == self.getToolHeadLocation(), f"Failed to home, expected {self.getHomePosition()} but got {self.getToolHeadLocation()}"
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def goTo(self, loc: Vector3, isVerbose: bool = False):
        """
        Move the tool head to a specific location.
        :param loc: the coordinates to move to
        :type loc: Vector3
        :param isVerbose: whether to log the command
        :type isVerbose: bool
        :return: True if the tool head is at the location, else False
        :rtype: bool
        :raises AssertionError: if the location is not a Vector3, if isVerbose is not a bool, or if self is not a Device
        """
        assert isinstance(loc, Vector3), f"Expected Vector3, got {type(loc)}"
        assert isinstance(isVerbose, bool), f"Expected bool, got {type(isVerbose)}"
        assert isinstance(self, Device), f"Expected Device, got {type(self)}"
        self.sendGcode(f"G0 X{loc.x} Y{loc.y} Z{loc.z} F{str(self.MAXFEEDRATE)}\n".encode("utf-8"), isVerbose=isVerbose)
        self.sendGcode(f'M114\n'.encode("utf-8"), isVerbose=isVerbose)
        if hasattr(self, "getLocationCMD"):
            return loc == self.getToolHeadLocation()
        return True

    def parseGcode(self, job: Job, isVerbose: bool = False) -> bool| Exception:
        """
        Parse a G-code file and send the commands to the device.
        :param Job job: The Job object, with file name to parse.
        :param bool isVerbose: Whether to log the commands
        :return: True if the job is complete, else the exception
        :rtype: bool | Exception
        :raises AssertionError: if the file is not a string or if isVerbose is not a bool
        """
        assert isinstance(job, Job), f"Expected Job object, got {type(job)}"
        file = job.file_path
        assert os.path.exists(file), f"File {file} does not exist"
        assert isinstance(file, str), f"Expected string, got {type(file)}"
        assert isinstance(isVerbose, bool), f"Expected bool, got {type(isVerbose)}"
        try:
            with open(file, "r") as f:
                if self.logger is not None: self.logger.info(f"Printing {file}")
                for line in f:
                    if line.startswith(";") or line == "\n":
                        continue
                    if current_app:
                        with current_app.app_context():
                            current_app.socketio.emit("gcode_line", {"line": line.strip("\n"), "printerid": self.dbID})
                    if isVerbose and self.logger: self.logger.debug(line.strip("\n"))
                    if self.status == "paused":
                        self.pause()
                        while self.status == "paused":
                            sleep(1)
                            if self.status == "cancelled":
                                if isinstance(self, hasEndingSequence):
                                    self.endSequence()
                                self.verdict = "cancelled"
                                if self.logger is not None: self.logger.info("Job cancelled")
                                return True
                            elif self.status == "printing":
                                self.resume()
                    if self.status == "cancelled":
                        if isinstance(self, hasEndingSequence):
                            self.endSequence()
                        self.verdict = "cancelled"
                        if self.logger is not None: self.logger.info("Job cancelled")
                        return True
                    if ";" in line:
                        line = line.split(";")[0].strip() + "\n"
                    self.sendGcode(line.encode("utf-8"), isVerbose=isVerbose)
            self.verdict = "complete"
            if self.logger is not None: self.logger.info("Job complete")
            return True
        except Exception as e:
            current_app.socketio.emit("error_update", {"fabricator_id": self.dbID, "job_id": job.id, "error": str(e)})
            current_app.handle_errors_and_logging(e, self.logger)
            self.verdict = "error"
            return e


    def pause(self) -> bool:
        """
        Pause the device, if the pause command is implemented.
        :rtype: bool
        """
        pass

    def resume(self) -> bool:
        """
        Resume the device, if the resume command is implemented.
        :rtype: bool
        """
        pass

    def sendGcode(self, gcode: bytes, isVerbose: bool = False) -> bool:
        """
        Send a G-code command to the device.
        :param bytes gcode: The line to send to the hardware
        :param bool isVerbose: Whether to log the command
        :rtype: bool
        :raises AssertionError: if the serial connection is not open, if gcode is not bytes, or if isVerbose is not a bool
        """
        assert isinstance(self, Device)
        assert self.serialConnection is not None
        assert self.serialConnection.is_open
        assert isinstance(gcode, bytes)
        assert isinstance(isVerbose, bool)
        self.serialConnection.write(gcode)
        if isVerbose:
            if self.logger is not None: self.logger.debug(gcode.decode("utf-8"))
            else: print(gcode.decode("utf-8"))
        return True

    def getToolHeadLocation(self, isVerbose: bool = False) -> Vector3:
        """
        Get the current location of the tool head.
        :param bool isVerbose: Whether to log the command
        :return: the current location of the tool head
        :rtype: Vector3
        """
        assert hasattr(self, "getLocationCMD")
        self.serialConnection.write(self.getLocationCMD)
        response = ""
        while not (("X:" in response) and ("Y:" in response) and ("Z:" in response)):
            response = self.serialConnection.read()
            if isVerbose and self.logger: self.logger.info(response)
        loc = LocationResponse(response)
        return Vector3(loc.x, loc.y, loc.z)

    def repair(self) -> str:
        """
        Attempt to repair the device connection by closing and reopening the serial connection.
        :rtype: str
        """
        try:
            if self.MODEL and "Ender" in self.MODEL:
                # If the device is an Ender, skip specific repair commands
                if self.logger is not None:
                    self.logger.info(f"Repair skipped for {self.MODEL}")
                return "Repair not necessary for Ender devices."

            if self.serialConnection:
                if self.logger is not None: self.logger.info("Closing existing connection for repair.")
                self.serialConnection.close()

            # Attempt to reconnect
            if self.logger is not None: self.logger.info("Attempting to reconnect for repair.")
            self.connect()

            if self.serialConnection and self.serialConnection.is_open:
                if self.logger is not None: self.logger.info("Repair successful: connection reopened.")
                return "Repair successful."
            else:
                return "Repair failed: unable to reopen connection."
        except Exception as e:
            if self.logger is not None: self.logger.error(f"Error during repair: {e}")
            return f"Repair failed with error: {e}"

    def diagnose(self) -> str:
        """
        Diagnose the device by sending basic G-code commands and checking responses.
        :rtype: str
        """
        try:
            if self.MODEL and "Ender" in self.MODEL:
                # If the device is an Ender, skip the diagnosis
                if self.logger is not None: self.logger.info(f"Diagnosis skipped for {self.MODEL}")
                return "Diagnosis not necessary for Ender devices."

            if self.logger is not None: self.logger.info("Starting device diagnosis.")
            if not self.connect():
                return "Diagnosis failed: unable to connect."

            if self.logger is not None: self.logger.info("Sending diagnostic G-code command (e.g., M115).")
            self.sendGcode(b"M115\n")

            response = self.serialConnection.read().strip()

            if response:
                if self.logger is not None: self.logger.info(f"Diagnosis response: {response}")
                return response
            else:
                return "Diagnosis failed: no response from device."
        except Exception as e:
            if self.logger is not None: self.logger.error(f"Error during diagnosis: {e}")
            return f"Diagnosis failed with error: {e}"

    def hardReset(self, newStatus: str):
        if self.serialConnection and self.serialConnection.is_open:
            self.serialConnection.close()
            self.serialConnection = None
        # Additional reset logic can be added here if needed.
        self.serialConnection = current_app.resource_manager.open_resource(self.serialPort)

    def getModel(self):
        return self.MODEL

    def getHWID(self):
        return self.serialConnection.hwid

    def getSerialConnection(self):
        return self.serialConnection

    def getSerialPort(self):
        return self.serialPort

    def getDescription(self):
        return self.DESCRIPTION

    def getHomePosition(self):
        return self.homePosition

    def getMaxFeedRate(self):
        return self.MAXFEEDRATE

class LocationResponse:
    def __init__(self, response: str):
        import re
        loc = [item.strip() for item in re.split(r' Count X:| Count Y:| Count Z:|X:| Y:| Z:| E:|\n', response) if item]
        self.x = float(loc[0])
        self.y = float(loc[1])
        self.z = float(loc[2])
        self.e = float(loc[3])
        self.count_x = float(loc[4]) if '.' in loc[4] else int(loc[4])
        self.count_y = float(loc[5]) if '.' in loc[5] else int(loc[5])
        self.count_z = float(loc[6]) if '.' in loc[6] else int(loc[6])

    def __to_JSON__(self) -> dict[str, float | int]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "e": self.e,
            "count_x": self.count_x,
            "count_y": self.count_y,
            "count_z": self.count_z,
        }