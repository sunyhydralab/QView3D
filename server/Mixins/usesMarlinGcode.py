from abc import ABCMeta
from time import sleep
from typing_extensions import Buffer

from Classes.Fabricators.Device import Device
from Classes.LocationResponse import LocationResponse
from Classes.Vector3 import Vector3
from Mixins.canPause import canPause
from Mixins.hasResponseCodes import checkOK, checkXYZ, alwaysTrue, checkBedTemp, checkExtruderTemp, hasResponsecodes


class usesMarlinGcode(canPause, hasResponsecodes, metaclass=ABCMeta):
    homeCMD: Buffer = "G28\n".encode("utf-8")
    cancelCMD: Buffer = "M112\n".encode("utf-8")
    keepAliveCMD: Buffer = "M113 S1\n".encode("utf-8")
    doNotKeepAliveCMD: Buffer = "M113 S0\n".encode("utf-8")
    statusCMD: Buffer = "M115\n".encode("utf-8")
    getLocationCMD: Buffer = "M114\n".encode("utf-8")
    pauseCMD: Buffer = "M601\n".encode("utf-8")
    resumeCMD: Buffer = "M602\n".encode("utf-8")
    getMachineNameCMD: Buffer = "M997\n".encode("utf-8")

    callablesHashtable = {
        "G0": [alwaysTrue, checkOK], # Move
        "G1": [alwaysTrue, checkOK], # Move
        "G28": [alwaysTrue, checkOK], # Home
        "G29": [alwaysTrue, checkOK], # Auto bed leveling
        "M73": [alwaysTrue, checkOK], # Set build percentage
        "M109": [alwaysTrue, checkExtruderTemp], # Wait for hotend to reach target temp
        "M114": [alwaysTrue, checkXYZ], # Get current position
        "M140": [alwaysTrue, checkOK], # Set bed temp
        "M190": [alwaysTrue, checkBedTemp], # Wait for bed to reach target temp
    }

    def goTo(self: Device, loc: Vector3, isVerbose: bool = False):
        self.sendGcode(f"G0 X{loc.x} Y{loc.y} Z{loc.z} F36000\n".encode("utf-8"), isVerbose=isVerbose)
        self.sendGcode(f'M114\n'.encode("utf-8"), isVerbose=isVerbose)
        return loc == self.getToolHeadLocation()

    def parseGcode(self: Device, file, isVerbose: bool = False):
        try:
            with open(file, "r") as f:
                for line in f:
                    if line.startswith(";") or line == "\n":
                        continue
                    if isVerbose:
                        print(line, end="")
                    self.sendGcode(line.encode("utf-8"), isVerbose=isVerbose)
            return True
        except Exception as e:
            print(e)
            return False


    def sendGcode(self: Device, gcode: Buffer, isVerbose: bool = False):
        assert isinstance(gcode, bytes)
        self.serialConnection.write(gcode)
        callables = usesMarlinGcode.callablesHashtable.get(gcode.decode("utf-8").split("\n")[0].split(" ")[0], [alwaysTrue, checkOK])
        if callables[0] != alwaysTrue:
            while not callables[0](self.serialConnection.readline()):
                pass
        if callables[1] != alwaysTrue:
            while True:
                try:
                    line = self.serialConnection.readline()
                    if "processing" in line.decode("utf-8"):
                        continue
                    if isVerbose: print(line)
                    if callables[1](line):
                        return True
                except Exception as e:
                    print(e)
                    return False


    def getToolHeadLocation(self: Device, isVerbose: bool = False) -> Vector3:
        self.serialConnection.write(usesMarlinGcode.getLocationCMD)
        response = ""
        while not (("X:" in response) and ("Y:" in response) and ("Z:" in response)):
            response = self.serialConnection.readline().decode("utf-8")
            if isVerbose: print(response)
        loc = LocationResponse(response)
        return Vector3(loc.x, loc.y, loc.z)


    def home(self: Device, isVerbose: bool = False):
        self.sendGcode(usesMarlinGcode.homeCMD, isVerbose=isVerbose)
        return self.getHomePosition() == self.getToolHeadLocation()


    def pause(self):
        self.sendGcode(usesMarlinGcode.keepAliveCMD)
        self.sendGcode(usesMarlinGcode.pauseCMD)


    def resume(self):
        self.sendGcode(usesMarlinGcode.doNotKeepAliveCMD)
        self.sendGcode(usesMarlinGcode.resumeCMD)


    def connect(self: Device):
        Device.connect(self)
        try:
            if self.serialConnection:
                self.serialConnection.write(b"M155 S1\n")
                return True
        except Exception as e:
            return e


    def disconnect(self: Device):
        if self.serialConnection:
            self.sendGcode(b"M155 S0\n")
            self.sendGcode(b"M104 S0\n")
            self.sendGcode(b"M140 S0\n")
            self.sendGcode(b"M84\n")
            self.serialConnection.close()
