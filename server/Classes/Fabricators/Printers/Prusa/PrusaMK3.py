from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS

from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3
from Mixins.hasResponseCodes import alwaysTrue, checkOK


class PrusaMK3(PrusaPrinter):
    MODEL = "MK3"
    PRODUCTID = 0x0002
    DESCRIPTION = "Original Prusa MK3 - CDC"
    MAXFEEDRATE = 12000
    homePosition = Vector3(0.2, -3.78, 0.15)
    cancelCMD = b"M603\n"

    def __init__(self, serialPort: ListPortInfo | SysFS, consoleLogger=None, fileLogger=None):
        super().__init__(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
        self.callablesHashtable["G28"] = [checkOK, checkOK]

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
            self.serialConnection = serial.Serial(self.serialPort.device, 115200, timeout=60)
            self.serialConnection.reset_input_buffer()
            from time import sleep
            sleep(7)
            if self.serialConnection and self.serialConnection.is_open:
                self.serialConnection.write(b"M155 S1\n")
                return True
        except Exception as e:
            from app import app
            with app.app_context():
                return app.handle_error_and_logging(e, self)