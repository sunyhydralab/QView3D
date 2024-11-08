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
    serialID: str | None = None
    serialConnection: serial.Serial | None = None
    serialPort: ListPortInfo | SysFS | None = None
    homePosition: Vector3 | None = None
    status: str = "idle"
    verdict: str = ""

    def __init__(self, serialPort: ListPortInfo | SysFS, consoleLogger=None, fileLogger=None):
        self.serialPort = serialPort
        self.serialID = serialPort.serial_number
        self.logger = Logger(self.serialPort.device, self.DESCRIPTION, consoleLogger=consoleLogger, fileLogger=fileLogger)
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
            # let the printer parent class deal with the error
            return e

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
        pass

    def hardReset(self, newStatus: str):
        if self.serialConnection.is_open:
            self.serialConnection.close()

        pass

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
