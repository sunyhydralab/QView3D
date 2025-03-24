from Classes.FabricatorConnection import FabricatorConnection
from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3
from Mixins.hasResponseCodes import checkOK, checkTime, checkXYZ
from globals import current_app
from globals import PID


class PrusaMK3(PrusaPrinter):
    MODEL = "MK3"
    PRODUCTID = PID.MK3
    DESCRIPTION = "Original Prusa MK3 - CDC"
    MAXFEEDRATE = 12000
    homePosition = Vector3(0.2, -3.78, 0.15)
    cancelCMD = "M603"
    homeCMD = "G28"
    keepAliveCMD = None
    doNotKeepAliveCMD = None
    startTimeCMD = "M107"

    callablesHashtable = {
        "M31": [checkTime, checkOK],  # Print time
        "G28": [checkOK],  # Home
        "G29.02": [checkOK, checkOK],
        "G29.01": [checkOK, checkXYZ, checkXYZ, checkOK],  # Auto bed leveling
        "M601": [] # Pause
    }

    callablesHashtable = {**PrusaPrinter.callablesHashtable, **callablesHashtable}

    def endSequence(self):
        self.sendGcode("M104 S0") # turn off extruder
        self.sendGcode("M140 S0") # turn off heatbed
        self.sendGcode("M107") # turn off fan
        self.sendGcode("G1 X0 Y210 F36000") # home X axis and push Y forward
        self.sendGcode("M84") # disable motors

    def getPrintTime(self):
        pass

    def connect(self):
        try:
            import serial
            self.serialConnection = FabricatorConnection.staticCreateConnection(self.serialPort, 115200, timeout=60)
            self.serialConnection.reset_input_buffer()
            from time import sleep
            sleep(4)
            assert self.serialConnection, "Serial Connection is None"
            assert self.serialConnection.is_open, "Serial Connection is closed"
            self.sendGcode("M155 S1")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)