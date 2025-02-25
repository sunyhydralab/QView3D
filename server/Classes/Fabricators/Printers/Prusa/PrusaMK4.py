from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3

class PrusaMK4(PrusaPrinter):
    MODEL = "MK4"
    PRODUCTID = 0x000D
    DESCRIPTION = "Original Prusa MK4 - CDC"
    MAXFEEDRATE = 36000
    homePosition = Vector3(14.0, -4.0, 2.0)
    startTimeCMD = "M569"

    def endSequence(self):
        self.sendGcode("M104 S0\n")  # ; turn off temperature
        self.sendGcode("M140 S0\n")  # ; turn off heatbed
        self.sendGcode("M107\n")  # ; turn off fan
        self.sendGcode("G1 X241 Y170 F3600\n")  # ; move to end position
        self.sendGcode("M84\n")

    def getPrintTime(self):
        pass

