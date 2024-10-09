from abc import ABC

from Classes.Fabricators.Printers.Ender.Ender3 import Ender3


class Ender3Pro(Ender3):
    MODEL = "Ender 3 Pro"
    DESCRIPTION = "Ender 3 Pro - CDC"

    def home(self):
        # TODO: make the home work without crashing the printer
        pass