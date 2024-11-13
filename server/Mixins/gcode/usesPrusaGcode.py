from abc import ABCMeta
from typing_extensions import Buffer
from Classes.Fabricators.Device import Device
from Mixins.gcode.usesMarlinGcode import usesMarlinGcode
from Mixins.hasResponseCodes import alwaysTrue, checkOK

class usesPrusaGcode(usesMarlinGcode, metaclass=ABCMeta):
    callablesHashtable = {
        "G29 P1": [alwaysTrue, checkOK],  # Auto bed leveling
        "G29 P9": [checkOK, checkOK],  # Auto bed leveling
        "M73": [alwaysTrue, checkOK],  # Set build percentage
    }

    callablesHashtable = {**usesMarlinGcode.callablesHashtable, **callablesHashtable}

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
        assert isinstance(self, usesPrusaGcode)
        callables = self.callablesHashtable.get(gcode.decode("utf-8").split("\n")[0].split(" ")[0], [alwaysTrue, checkOK])
        assert isinstance(self, Device)
        if callables[0] != alwaysTrue:
            line = ""
            while not callables[0](line):
                line = self.serialConnection.readline()
                if isVerbose: self.logger.debug(line)
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