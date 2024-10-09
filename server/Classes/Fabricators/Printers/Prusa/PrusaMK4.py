from Classes.Fabricators.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3


class PrusaMK4(PrusaPrinter):
    MODEL = "Prusa MK4"
    PRODUCTID = 0x000D
    DESCRIPTION = "Original Prusa MK4 - CDC"
    homePosition = Vector3(14.0, -4.0, 2.0)

    def endSequence(self):
        # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+1, max_print_height)} F720 ; Move print head up{endif}")
        self.gcodeEnding("M104 S0")  # ; turn off temperature
        self.gcodeEnding("M140 S0")  # ; turn off heatbed
        self.gcodeEnding("M107")  # ; turn off fan

