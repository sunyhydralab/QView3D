from abc import ABCMeta
from time import sleep
from typing_extensions import Buffer

from Classes.Fabricators.Device import Device
from Classes.LocationResponse import LocationResponse
from Classes.Vector3 import Vector3
from Mixins.canPause import canPause
from Mixins.gcode.usesVanillaGcode import usesVanillaGcode
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import checkOK, checkXYZ, alwaysTrue, checkBedTemp, checkExtruderTemp, hasResponsecodes


class usesMarlinGcode(usesVanillaGcode, canPause, hasResponsecodes, metaclass=ABCMeta):
    cancelCMD: Buffer = b"M112\n"
    keepAliveCMD: Buffer = b"M113 S1\n"
    doNotKeepAliveCMD: Buffer = b"M113 S0\n"
    statusCMD: Buffer = b"M115\n"
    getLocationCMD: Buffer = b"M114\n"
    pauseCMD: Buffer = b"M601\n"
    resumeCMD: Buffer = b"M602\n"
    getMachineNameCMD: Buffer = b"M997\n"

    callablesHashtable = {
        "G29 P1": [alwaysTrue, checkOK], # Auto bed leveling
        "G29 P9": [checkOK, checkOK], # Auto bed leveling
        "M73": [alwaysTrue, checkOK], # Set build percentage
        "M104": [alwaysTrue, alwaysTrue], # Set hotend temp
        "M109": [alwaysTrue, checkExtruderTemp], # Wait for hotend to reach target temp
        "M114": [alwaysTrue, checkXYZ], # Get current position
        "M140": [alwaysTrue, alwaysTrue], # Set bed temp
        "M155": [alwaysTrue, alwaysTrue], # Set temperature auto report
        "M190": [alwaysTrue, checkBedTemp], # Wait for bed to reach target temp
    }

    callablesHashtable = {**usesVanillaGcode.callablesHashtable, **callablesHashtable}

    def goTo(self: Device, loc: Vector3, isVerbose: bool = False):
        assert isinstance(loc, Vector3)
        assert isinstance(isVerbose, bool)
        assert isinstance(self, Device)
        self.sendGcode(f"G0 X{loc.x} Y{loc.y} Z{loc.z} F{int(self.MAXFEEDRATE)}\n".encode("utf-8"), isVerbose=isVerbose)
        self.sendGcode(f'M114\n'.encode("utf-8"), isVerbose=isVerbose)
        return loc == self.getToolHeadLocation()

    def parseGcode(self: Device, file: str, isVerbose: bool = False):
        assert isinstance(file, str)
        assert isinstance(isVerbose, bool)
        assert isinstance(self, Device)
        try:
            with open(file, "r") as f:
                self.logger.info(f"Printing {file}")
                for line in f:
                    if line.startswith(";") or line == "\n":
                        continue
                    if isVerbose: self.logger.debug(line.strip("\n"))
                    if self.status == "paused":
                        self.pause()
                        while self.status == "paused":
                            sleep(1)
                        if self.status == "cancelled":
                            if isinstance(self, hasEndingSequence):
                                self.endSequence()
                            self.verdict = "cancelled"
                            self.logger.info("Job cancelled")
                            return True
                        elif self.status == "printing":
                            self.resume()
                    if self.status == "cancelled":
                        if isinstance(self, hasEndingSequence):
                            self.endSequence()
                        self.verdict = "cancelled"
                        self.logger.info("Job cancelled")
                        return True
                    self.sendGcode(line.encode("utf-8"), isVerbose=isVerbose)
            self.verdict = "complete"
            self.logger.info("Job complete")
            return True
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error cancelling job:")
                self.logger.error(e)
            self.verdict = "error"
            return True


    def sendGcode(self: Device, gcode: Buffer, isVerbose: bool = False):
        assert self.serialConnection.is_open
        assert isinstance(gcode, bytes)
        self.serialConnection.write(gcode)
        hashIndex = gcode.decode("utf-8").split("\n")[0].split(" ")[0]
        if hashIndex == "G29":
            g29addon = gcode.decode("utf-8").split("\n")[0].split(" ")[1]
            if g29addon == "P9":
                hashIndex += " " + g29addon
            else:
                hashIndex += " P1"
        elif hashIndex == "M109" or hashIndex == "M190":
            self.logger.info("Waiting for temperature to stabilize...")
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
                    if isVerbose: self.logger.debug(line)
                    if callables[1](line):
                        self.logger.info(gcode.decode().strip() + ": " + line.decode().strip())
                        return True
                except UnicodeDecodeError as e:
                      continue
                except Exception as e:
                    self.logger.error(e)
                    return False


    def getToolHeadLocation(self: Device, isVerbose: bool = False) -> Vector3:
        self.serialConnection.write(usesMarlinGcode.getLocationCMD)
        response = ""
        while not (("X:" in response) and ("Y:" in response) and ("Z:" in response)):
            response = self.serialConnection.readline().decode("utf-8")
            if isVerbose: self.logger.info(response)
        loc = LocationResponse(response)
        return Vector3(loc.x, loc.y, loc.z)


    def home(self, isVerbose: bool = False):
        try:
            assert isinstance(isVerbose, bool)
            assert isinstance(self, Device)
            self.sendGcode(usesMarlinGcode.homeCMD, isVerbose=isVerbose)
            return self.getHomePosition() == self.getToolHeadLocation()
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error homing:")
                self.logger.error(e)
            return


    def pause(self):
        try:
            assert isinstance(self, canPause)
            assert isinstance(self, Device)
            assert self.serialConnection is not None
            assert self.serialConnection.is_open
            assert self.status == "printing"
            self.sendGcode(usesMarlinGcode.keepAliveCMD)
            self.sendGcode(usesMarlinGcode.pauseCMD)
            self.logger.info("Job Paused")
            return True
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error pausing job:")
                self.logger.error(e)
            return False

    def resume(self):
        try:
            assert isinstance(self, canPause)
            assert isinstance(self, Device)
            assert self.serialConnection is not None
            assert self.serialConnection.is_open
            assert self.status == "paused"
            self.sendGcode(usesMarlinGcode.doNotKeepAliveCMD)
            self.sendGcode(usesMarlinGcode.resumeCMD)
            self.logger.info("Job Resumed")
            return True
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error resuming job:")
                self.logger.error(e)
            return False


    def connect(self: Device):
        Device.connect(self)
        try:
            if self.serialConnection:
                self.serialConnection.write(b"M155 S1\n")
                return True
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error connecting:")
                self.logger.error(e)
            return False


    def disconnect(self: Device):
        if self.serialConnection and self.serialConnection.is_open:
            self.sendGcode(b"M155 S100\n")
            self.sendGcode(b"M155 S0\n")
            self.sendGcode(b"M104 S0\n")
            self.sendGcode(b"M140 S0\n")
            self.sendGcode(b"M84\n")
            self.serialConnection.close()
