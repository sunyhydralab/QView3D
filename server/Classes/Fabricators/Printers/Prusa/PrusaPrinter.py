from abc import ABCMeta
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import checkXYZ, checkOK, checkTime


class PrusaPrinter(Printer, hasEndingSequence, metaclass=ABCMeta):
    VENDORID = 0x2C99
    cancelCMD: bytes = b"M112\n"
    keepAliveCMD: bytes = b"M113 S1\n"
    doNotKeepAliveCMD: bytes = b"M113 S0\n"
    statusCMD: bytes = b"M115\n"
    getLocationCMD: bytes = b"M114\n"
    pauseCMD: bytes = b"M601\n"
    resumeCMD: bytes = b"M602\n"

    callablesHashtable = {
        "G28": [checkXYZ, checkOK],  # Home
        "G29.01": [checkXYZ, checkOK],  # Auto bed leveling
        "G29.02": [checkOK],  # Auto bed leveling
        "M31": [checkOK, checkTime, checkOK],  # Print time
        "M73": [checkOK],  # Set build percentage
    }

    callablesHashtable = {**Printer.callablesHashtable, **callablesHashtable}


    def extractIndex(self, gcode: bytes) -> str:
        hashIndex = gcode.decode().split("\n")[0].split(" ")[0]
        if hashIndex == "G29":
            try:
                g29addon = gcode.decode().split("\n")[0].split(" ")[1]
                hashIndex += ".01" if g29addon == "P1" else ".02"
            except IndexError as e:
                hashIndex += ".01"
        if self.logger is not None:
            if hashIndex == "M109" or hashIndex == "M190":
                self.logger.info("Waiting for temperature to stabilize...")
            elif hashIndex == "G28":
                self.logger.info("Homing...")
        return hashIndex
