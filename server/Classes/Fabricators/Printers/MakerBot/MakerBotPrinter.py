from abc import ABCMeta
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes

class MakerBotPrinter(Printer, hasEndingSequence, hasResponsecodes, metaclass=ABCMeta):
    VENDORID = 0x23C1
    homePosition = Vector3(0.0, 0.0, 0.0)