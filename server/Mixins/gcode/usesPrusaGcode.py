from abc import ABCMeta
from typing_extensions import Buffer
from Classes.Fabricators.Device import Device
from Mixins.gcode.usesMarlinGcode import usesMarlinGcode
from Mixins.hasResponseCodes import checkOK, checkXYZ, checkTime

class usesPrusaGcode(usesMarlinGcode, metaclass=ABCMeta):
    callablesHashtable = {
        "G28": [checkXYZ, checkOK],  # Home
        "G29.01": [checkXYZ, checkOK],  # Auto bed leveling
        "G29.02": [checkOK],  # Auto bed leveling
        "M31": [checkOK, checkTime, checkOK],  # Print time
        "M73": [checkOK],  # Set build percentage
    }

    callablesHashtable = {**usesMarlinGcode.callablesHashtable, **callablesHashtable}

    def sendGcode(self: Device, gcode: Buffer, isVerbose: bool = False):
        assert self.serialConnection.is_open
        assert isinstance(gcode, bytes)
        self.serialConnection.write(gcode)
        hashIndex = gcode.decode("utf-8").split("\n")[0].split(" ")[0]
        if hashIndex == "G29":
            try:
                g29addon = gcode.decode("utf-8").split("\n")[0].split(" ")[1]
                hashIndex += ".01" if g29addon == "P1" else ".02"
            except IndexError as e:
                hashIndex += ".01"
        if hashIndex == "M109" or hashIndex == "M190":
            self.logger.info("Waiting for temperature to stabilize...")
        elif hashIndex == "G28":
            self.logger.info("Homing...")
        assert isinstance(self, usesPrusaGcode)
        callables = self.callablesHashtable.get(hashIndex, [checkOK])
        assert isinstance(self, Device)
        line=''
        for func in callables:
            while True:
                if self.status == "cancelled": return True
                try:
                    line = self.serialConnection.readline()
                    if "processing" in line.decode("utf-8"): continue
                    if isVerbose: self.logger.debug(f"{gcode.decode().strip()}: {line.decode().strip()}")
                    if func(line):
                        break
                except UnicodeDecodeError as e:
                    if isVerbose: self.logger.debug(f"{gcode.decode().strip()}: {line.strip()}")
                    continue
                except Exception as e:
                    self.logger.error(e)
                    return False
        if not callables: self.logger.info(f"{gcode.decode().strip()}: Always True")
        else: self.logger.info(gcode.decode().strip() + ": " + (line.decode() if isinstance(line, bytes) else line).strip())
        return True