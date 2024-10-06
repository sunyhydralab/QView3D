from abc import ABC
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from Classes.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Interfaces.hasEndingSequence import hasEndingSequence
from Interfaces.hasResponseCodes import hasResponsecodes


class PrusaMK3(ABC, PrusaPrinter, hasEndingSequence, hasResponsecodes):
    __MODEL = "Prusa MK3"
    __PRODUCTID = 0x0002
    __DESCRIPTION = "Original Prusa MK3 - CDC"

    def __init__(self, serialPort: ListPortInfo | SysFS):
        super().__init__(self, serialPort)

    def endSequence(self):
        self.gcodeEnding("M104 S0") # turn off extruder
        self.gcodeEnding("M140 S0") # turn off heatbed
        self.gcodeEnding("M107") # turn off fan
        self.gcodeEnding("G1 X0 Y210") # home X axis and push Y forward
        self.gcodeEnding("M84") # disable motors