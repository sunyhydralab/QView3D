from abc import ABCMeta
from typing import Callable
from typing_extensions import Buffer

from Classes.Fabricators.Device import Device
from Classes.LocationResponse import LocationResponse
from Classes.Vector3 import Vector3
from Mixins.hasResponseCodes import checkOK, checkXYZ


class usesMarlinGcode(metaclass=ABCMeta):
    homeCMD: Buffer = "G28\n".encode("utf-8")
    pause: Buffer = "M601\n".encode("utf-8") + "M113 S1\n".encode("utf-8")
    resume: Buffer = "M602\n".encode("utf-8")
    cancel: Buffer = "M112\n".encode("utf-8")
    status: Buffer = "M115\n".encode("utf-8")
    getLocation: Buffer = "M114\n".encode("utf-8")
    getMachineName: Buffer = "M997\n".encode("utf-8")

    def goTo(self: Device, loc: Vector3, isVerbose: bool = False):
        self.sendGcode(f"G0 X{loc.x} Y{loc.y} Z{loc.z}\n".encode("utf-8"), checkXYZ, isVerbose=isVerbose)
        return loc == self.getPrintHeadLocation()

    def parseGcode(self, file):
        with open(file, "r") as f:
            for line in f:
                self.sendGcode(line.encode("utf-8"), checkOK)


    def sendGcode(self: Device, gcode: Buffer, checkFunction: Callable, isVerbose: bool = False):
        assert callable(checkFunction)
        assert isinstance(gcode, bytes)
        self.serialConnection.write(gcode)
        while self.serialConnection.readline() == b'ok\n':
            pass
        while True:
            try:
                line = self.serialConnection.readline()
                if isVerbose: print(line)
                if checkFunction(line):
                    break
            except Exception as e:
                print(e)
                break

    def getPrintHeadLocation(self: Device, isVerbose: bool = False) -> Vector3:
        self.serialConnection.write(usesMarlinGcode.getLocation)
        response = ""
        while not (("X:" in response) and ("Y:" in response) and ("Z:" in response)):
            response = self.serialConnection.readline().decode("utf-8")
            if isVerbose: print(response)
        loc = LocationResponse(response)
        return Vector3(loc.x, loc.y, loc.z)

    def home(self: Device, isVerbose: bool = False):
        self.sendGcode("G28\n".encode("utf-8"), checkOK, isVerbose=isVerbose)
        return self.getHomePosition() == self.getPrintHeadLocation()

    def connect(self: Device):
        Device.connect(self)
        try:
            if self.serialConnection:
                self.serialConnection.write("M155 S5 C7\n".encode("utf-8"))
                return True
        except Exception as e:
            return e

    def disconnect(self: Device):
        if self.serialConnection:
            self.serialConnection.write("M155 S0\n".encode("utf-8") + "M84\n".encode("utf-8"))
            self.serialConnection.close()