from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter

class PrusaMK3(PrusaPrinter):
    MODEL = "Prusa MK3"
    PRODUCTID = 0x0002
    DESCRIPTION = "Original Prusa MK3 - CDC"

    def endSequence(self):
        self.gcodeEnding("M104 S0") # turn off extruder
        self.gcodeEnding("M140 S0") # turn off heatbed
        self.gcodeEnding("M107") # turn off fan
        self.gcodeEnding("G1 X0 Y210") # home X axis and push Y forward
        self.gcodeEnding("M84") # disable motors