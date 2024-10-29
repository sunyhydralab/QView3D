from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter

class PrusaMK3(PrusaPrinter):
    MODEL = "Prusa MK3"
    PRODUCTID = 0x0002
    DESCRIPTION = "Original Prusa MK3 - CDC"

    def endSequence(self):
        self.sendGcode(b"M104 S0\n") # turn off extruder
        self.sendGcode(b"M140 S0\n") # turn off heatbed
        self.sendGcode(b"M107\n") # turn off fan
        self.sendGcode(b"G1 X0 Y210\n") # home X axis and push Y forward
        self.sendGcode(b"M84\n") # disable motors

    def getPrintTime(self):
        pass