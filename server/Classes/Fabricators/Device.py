from abc import ABC, abstractmethod
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from typing_extensions import Buffer
from Classes.Vector3 import Vector3
from Classes.Logger import Logger
import serial
import serial.tools.list_ports
from Mixins.canPause import canPause

class Device(ABC):
    # static variables
    MODEL: str | None = None
    VENDORID: int | None = None
    PRODUCTID: int | None = None
    DESCRIPTION: str | None = None
    MAXFEEDRATE: int | None = None
    serialConnection: serial.Serial | None = None
    homePosition: Vector3 | None = None

    def __init__(self, serialPort: ListPortInfo | SysFS, consoleLogger=None, fileLogger=None):
        self.serialPort: ListPortInfo | SysFS | None = serialPort
        self.serialID: str | None = serialPort.serial_number
        self.logger = Logger(self.DESCRIPTION, port=self.serialPort.device, consoleLogger=consoleLogger, fileLogger=fileLogger)
        self.status = "idle"
        self.verdict = ""

    def __repr__(self):
        return f"{self.getModel()} on {self.getSerialPort().device}"

    def connect(self):
        try:
            self.serialConnection = serial.Serial(self.serialPort.device, 115200, timeout=60)
            self.serialConnection.reset_input_buffer()
            return True
        except Exception as e:
            from app import app
            with app.app_context():
                return app.handle_error_and_logging(e, self)
    def disconnect(self):
        if self.serialConnection:
            self.serialConnection.close()
            self.serialConnection = None

    @abstractmethod
    def home(self, isVerbose: bool = False):
        pass

    @abstractmethod
    def goTo(self, loc: Vector3, isVerbose: bool = False):
        pass

    def parseGcode(self, file, isVerbose=False):
        pass

    def pause(self: canPause):
        pass

    def resume(self: canPause):
        pass

    @abstractmethod
    def sendGcode(self, gcode: Buffer, isVerbose: bool = False):
        pass

    @abstractmethod
    def getToolHeadLocation(self) -> Vector3:
        pass

    def repair(self):
        """Attempt to repair the device connection by closing and reopening the serial connection."""
        try:
            if self.MODEL and "Ender" in self.MODEL:
                # If the device is an Ender, skip specific repair commands
                if self.logger:
                    self.logger.info(f"Repair skipped for {self.MODEL}")
                return "Repair not necessary for Ender devices."

            if self.serialConnection:
                self.logger.info("Closing existing connection for repair.")
                self.serialConnection.close()

            # Attempt to reconnect
            self.logger.info("Attempting to reconnect for repair.")
            self.connect()

            if self.serialConnection and self.serialConnection.is_open:
                self.logger.info("Repair successful: connection reopened.")
                return "Repair successful."
            else:
                return "Repair failed: unable to reopen connection."
        except Exception as e:
            self.logger.error(f"Error during repair: {e}")
            return f"Repair failed with error: {e}"

    def diagnose(self):
        """Diagnose the device by sending basic G-code commands and checking responses."""
        try:
            if self.MODEL and "Ender" in self.MODEL:
                # If the device is an Ender, skip the diagnosis
                self.logger.info(f"Diagnosis skipped for {self.MODEL}")
                return "Diagnosis not necessary for Ender devices."

            self.logger.info("Starting device diagnosis.")
            if not self.connect():
                return "Diagnosis failed: unable to connect."

            self.logger.info("Sending diagnostic G-code command (e.g., M115).")
            self.sendGcode(b"M115\n")

            response = self.serialConnection.readline().decode("utf-8").strip()
            self.disconnect()

            if response:
                self.logger.info(f"Diagnosis response: {response}")
                return f"Diagnosis successful: {response}"
            else:
                return "Diagnosis failed: no response from device."
        except Exception as e:
            self.logger.error(f"Error during diagnosis: {e}")
            return f"Diagnosis failed with error: {e}"

    def hardReset(self, newStatus: str):
        if self.serialConnection and self.serialConnection.is_open:
            self.serialConnection.close()
        # Additional reset logic can be added here if needed.

    def getModel(self):
        return self.MODEL

    def getHWID(self):
        return self.serialPort.hwid.split(' LOCATION=')[0]

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
