from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3

class PrusaMK4(PrusaPrinter):
    MODEL = "Prusa MK4"
    PRODUCTID = 0x000D
    DESCRIPTION = "Original Prusa MK4 - CDC"
    MAXFEEDRATE = 36000
    homePosition = Vector3(14.0, -4.0, 2.0)

    def endSequence(self):
        # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+1, max_print_height)} F720 ; Move print head up{endif}")
        self.sendGcode(b"M104 S0\n")  # ; turn off temperature
        self.sendGcode(b"M140 S0\n")  # ; turn off heatbed
        self.sendGcode(b"M107\n")  # ; turn off fan
        self.sendGcode(b"G1 X241 Y170 F3600")

    def getPrintTime(self):
        pass

