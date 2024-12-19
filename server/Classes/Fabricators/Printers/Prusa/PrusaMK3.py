from Classes.FabricatorConnection import FabricatorConnection
from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3
from Mixins.hasResponseCodes import checkOK, checkTime, checkXYZ
from globals import current_app


class PrusaMK3(PrusaPrinter):
    MODEL = "MK3"
    PRODUCTID = 0x0002
    DESCRIPTION = "Original Prusa MK3 - CDC"
    MAXFEEDRATE = 12000
    homePosition = Vector3(0.2, -3.78, 0.15)
    cancelCMD = b"M603\n"
    homeCMD = b"G28\n"
    keepAliveCMD = None
    doNotKeepAliveCMD = None
    startTimeCMD = "M107"

    callablesHashtable = {
        "M31": [checkTime, checkOK],  # Print time
        "G28": [checkOK, checkOK],  # Home
        "G29.02": [checkOK, checkOK],
        "G29.01": [checkOK, checkXYZ, checkXYZ, checkOK],  # Auto bed leveling
        "M601": [] # Pause
    }

    callablesHashtable = {**PrusaPrinter.callablesHashtable, **callablesHashtable}

    def endSequence(self):
        self.sendGcode(b"M104 S0\n") # turn off extruder
        self.sendGcode(b"M140 S0\n") # turn off heatbed
        self.sendGcode(b"M107\n") # turn off fan
        self.sendGcode(b"G1 X0 Y210 F36000\n") # home X axis and push Y forward
        self.sendGcode(b"M84\n") # disable motors

    def getPrintTime(self):
        pass

    def connect(self):
        try:
            import serial
            self.serialConnection = FabricatorConnection.staticCreateConnection(self.serialPort.device, 115200, timeout=60)
            self.serialConnection.reset_input_buffer()
            from time import sleep
            sleep(4)
            if self.serialConnection and self.serialConnection.is_open:
                self.sendGcode(b"M155 S1\n")
                return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)