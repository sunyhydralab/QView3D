from abc import ABC

from Classes.Printers.Ender.Ender3 import Ender3


class Ender3Pro(ABC, Ender3):
    __MODEL = "Ender 3 Pro"
    __DESCRIPTION = "Ender 3 Pro - CDC"

    def __init__(self, serialPort):
        super().__init__(self, serialPort)

    def home(self):
        # TODO: make the home work without crashing the printer
        pass