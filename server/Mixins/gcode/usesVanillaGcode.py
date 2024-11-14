from time import sleep

from typing_extensions import Buffer

from Classes.Fabricators.Device import Device
from Classes.Vector3 import Vector3
from Mixins.hasResponseCodes import checkXYZ


class usesVanillaGcode:
    homeCMD: Buffer = b"G28\n"

    callablesHashtable = {
        "G28": [checkXYZ],  # Home
    }

    def goTo(self: Device, loc: Vector3, isVerbose: bool = False):
        assert isinstance(loc, Vector3)
        assert isinstance(isVerbose, bool)
        assert isinstance(self, Device)
        self.sendGcode(f"G0 X{loc.x} Y{loc.y} Z{loc.z} F{str(self.MAXFEEDRATE)}\n".encode("utf-8"), isVerbose=isVerbose)

    def home(self, isVerbose: bool = False):
        try:
            assert isinstance(isVerbose, bool)
            assert isinstance(self, Device)
            self.sendGcode(usesVanillaGcode.homeCMD, isVerbose=isVerbose)
            return True
        except Exception as e:
            if self.logger is None:
                print(e)
            else:
                self.logger.error("Error homing:")
                self.logger.error(e)
            return

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
                            self.verdict = "cancelled"
                            self.logger.info("Job cancelled")
                            return True
                        elif self.status == "printing":
                            self.resume()
                    if self.status == "cancelled":
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
        self.logger.debug(gcode.decode("utf-8"))
        return True
