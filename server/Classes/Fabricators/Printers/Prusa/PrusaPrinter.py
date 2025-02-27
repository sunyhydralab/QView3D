from abc import ABCMeta
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import checkXYZ, checkOK, checkTime
from globals import current_app, VID

class PrusaPrinter(Printer, hasEndingSequence, metaclass=ABCMeta):
    VENDORID = VID.PRUSA
    cancelCMD: str = "M112"
    keepAliveCMD: str = "M113 S1"
    doNotKeepAliveCMD: str = "M113 S0"
    statusCMD: str = "M115"
    getLocationCMD: str = "M114"
    pauseCMD: str = "M601"
    resumeCMD: str = "M602"

    callablesHashtable = {
        "G28": [checkXYZ, checkOK],  # Home
        "G29.01": [checkXYZ, checkOK],  # Auto bed leveling
        "G29.02": [checkOK],  # Auto bed leveling
        "M31": [checkOK, checkTime, checkOK],  # Print time
    }

    callablesHashtable = {**Printer.callablesHashtable, **callablesHashtable}

    def extractIndex(self, gcode: str, logger=None) -> str:
        hashIndex = super().extractIndex(gcode, logger)
        if hashIndex == "G29":
            try:
                g29addon = gcode.split("\n")[0].split(" ")[1]
                hashIndex += ".01" if g29addon == "P1" else ".02"
            except IndexError:
                hashIndex += ".01"
            if hashIndex == "G29.01":
                if logger is not None: logger.info("Auto bed leveling...")
                current_app.socketio.emit("console_update", {"message": "Auto bed leveling...", "level": "info", "printerid": self.dbID})
        return hashIndex
