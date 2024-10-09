from abc import ABC, abstractmethod

from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from typing_extensions import Buffer

# from Classes.Fabricators.Printers.Ender.Ender3Pro import Ender3Pro
# from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
# from Classes.Fabricators.Printers.Ender.EnderPrinter import EnderPrinter
# from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
# from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
# from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
# from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3
import serial
import serial.tools.list_ports

class Device(ABC):
    # static variables
    MODEL: str | None = None
    VENDORID: int | None = None
    PRODUCTID: int | None = None
    DESCRIPTION: str | None = None
    serialID: str | None = None
    serialConnection: serial.Serial | None = None
    serialPort: ListPortInfo | SysFS | None = None
    homePosition: Vector3 | None = None

    def __init__(self, serialPort: ListPortInfo | SysFS):
        self.serialPort = serialPort
        self.serialID = serialPort.serial_number

    def __repr__(self):
        return f"{self.getModel()} on {self.getSerialPort().device}"

    # @staticmethod
    # def createDevice(serialPort: ListPortInfo | SysFS | None):
    #     """creates the correct printer object based on the serial port info"""
    #     if serialPort is None:
    #         return None
    #     if serialPort.vid == PrusaPrinter.__VENDORID:
    #         if serialPort.pid == PrusaMK4.__PRODUCTID:
    #             return PrusaMK4(serialPort)
    #         elif serialPort.pid == PrusaMK4S.__PRODUCTID:
    #             return PrusaMK4S(serialPort)
    #         elif serialPort.pid == PrusaMK3.__PRODUCTID:
    #             return PrusaMK3(serialPort)
    #         else:
    #             return None
    #     elif serialPort.vid == EnderPrinter.__VENDORID:
    #         if serialPort.pid == Ender3.__PRODUCTID:
    #             return Ender3(serialPort)
    #         elif serialPort.pid == Ender3Pro.__PRODUCTID:
    #             return Ender3Pro(serialPort)


    def connect(self):
        try:
            self.serialConnection = serial.Serial(self.serialPort.device, 115200, timeout=10)
            return True
        except Exception as e:
            # let the printer parent class deal with the error
            return e

    def disconnect(self):
        if self.serialConnection:
            self.serialConnection.close()
            self.serialConnection = None

    @abstractmethod
    def home(self):
        pass

    def parseGcode(self):
        pass

    def sendGcode(self, gcode: Buffer, checkFunction):
        pass

    def repair(self):
        pass

    def hardReset(self, newStatus: str):
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
