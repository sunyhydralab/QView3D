from abc import ABC
from serial.tools.list_ports_common import ListPortInfo
from Classes.Printers.Prusa.PrusaMK4 import PrusaMK4

class PrusaMK4S(PrusaMK4, ABC):
    __MODEL = "Prusa MK4S"
    __PRODUCTID = 0x001A
    __DESCRIPTION = "Original Prusa MK4S - CDC"

    def __init__(self, serialPort: ListPortInfo):
        super().__init__(self, serialPort)
