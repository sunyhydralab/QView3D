from abc import ABCMeta
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from globals import VID


class MakerBotPrinter(Printer, metaclass=ABCMeta):
    VENDORID = VID.MAKERBOT
    homePosition = Vector3(0.0, 0.0, 0.0)