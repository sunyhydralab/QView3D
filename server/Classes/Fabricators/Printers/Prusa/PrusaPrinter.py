from abc import ABCMeta
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import checkXYZ, checkOK, checkTime
from globals import current_app

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
    }

    callablesHashtable = {**Printer.callablesHashtable, **callablesHashtable}

    def extractIndex(self, gcode: bytes, logger=None) -> str:
        hashIndex = super().extractIndex(gcode, logger)
        if hashIndex == "G29":
            try:
                g29addon = gcode.decode().split("\n")[0].split(" ")[1]
                hashIndex += ".01" if g29addon == "P1" else ".02"
            except IndexError:
                hashIndex += ".01"
            if hashIndex == "G29.01":
                current_app.socketio.emit("console_update", {"message": "Auto bed leveling...", "level": "info", "printerid": self.dbID})
        return hashIndex
