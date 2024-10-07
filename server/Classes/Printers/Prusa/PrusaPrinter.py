from abc import ABC
from serial.tools.list_ports_common import ListPortInfo
from Classes.Vector3 import Vector3
from Classes.Device import Device
from Interfaces.canPause import canPause
from Interfaces.hasEndingSequence import hasEndingSequence
from Interfaces.hasResponseCodes import hasResponsecodes


class PrusaPrinter(ABC, Device, hasEndingSequence, hasResponsecodes, canPause):
    __VENDORID = 0x2C99

    def __init__(self, serialPort: ListPortInfo):
        super().__init__(self, serialPort)

    def home(self):
        self.__serialConnection.write("G28\n".encode("utf-8"))
        while self.getPrintHeadLocation() != self.__homeLocation:
            pass
        return True


    def endSequence(self):
        pass

    def getPrintHeadLocation(self) -> Vector3:
        self.__serialConnection.write("M114\n".encode("utf-8"))
        response = self.__serialConnection.readline().decode("utf-8")
        x = float(response.split("X:")[1].split(" ")[0])
        y = float(response.split("Y:")[1].split(" ")[0])
        z = float(response.split("Z:")[1].split(" ")[0])
        return Vector3(x,y,z)

    def connect(self):
        try:
            super().connect()
            if self.__serialConnection:
                self.__serialConnection.write("M155 S5 C7\n".encode("utf-8"))
                return True
        except Exception as e:
            return e

    def disconnect(self):
        if self.__serialConnection:
            self.__serialConnection.write(f"M155 S0\n".encode("utf-8"))
            self.__serialConnection.close()
            self.__serialConnection = None

    def pause(self):
        self.__serialConnection.write("M601\n".encode("utf-8"))
        self.__serialConnection.write("M113 S1\n".encode("utf-8"))

    def resume(self):
        self.__serialConnection.write("M602\n".encode("utf-8"))

    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is PrusaPrinter:
            if any("Prusa" in B.__dict__.get('__DESCRIPTION__', '') for B in subclass.__mro__):
                return True
        return NotImplemented
