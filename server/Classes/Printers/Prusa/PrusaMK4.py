from abc import ABC
from serial.tools.list_ports_common import ListPortInfo
from Classes.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Interfaces.hasEndingSequence import hasEndingSequence
from Interfaces.hasResponseCodes import hasResponsecodes


class PrusaMK4(ABC, PrusaPrinter, hasEndingSequence, hasResponsecodes):
    __MODEL = "Prusa MK4"
    __PRODUCTID = 0x000D
    __DESCRIPTION = "Original Prusa MK4 - CDC"

    def __init__(self, serialPort: ListPortInfo):
        super().__init__(self, serialPort)

    def endSequence(self):
        # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+1, max_print_height)} F720 ; Move print head up{endif}")
        self.gcodeEnding("M104 S0")  # ; turn off temperature
        self.gcodeEnding("M140 S0")  # ; turn off heatbed
        self.gcodeEnding("M107")  # ; turn off fan

