from abc import ABC

from Classes.Printers.Ender.EnderPrinter import EnderPrinter


class Ender3(ABC, EnderPrinter):
    __MODEL = "Ender 3"
    __PRODUCTID = 0x7523
    __DESCRIPTION = "Ender 3 - CDC"

    def __init__(self, serialPort):
        super().__init__(self, serialPort)