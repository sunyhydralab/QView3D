from abc import ABCMeta
from typing import Callable
from typing_extensions import Buffer
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes, checkOK, alwaysTrue
from Mixins.usesMarlinGcode import usesMarlinGcode

class MakerBotPrinter(Printer, hasEndingSequence, hasResponsecodes, metaclass=ABCMeta):
    VENDORID = 0x23C1
    homePosition = Vector3(0.0, 0.0, 0.0)

    def connect(self):
        return usesMarlinGcode.connect(self)

    def disconnect(self):
        return usesMarlinGcode.disconnect(self)

    def endSequence(self):
        pass

    def goTo(self, loc: Vector3, isVerbose: bool = False):
        pass

    def getPrintTime(self):
        pass

    def getToolHeadLocation(self) -> Vector3:
        pass

    def parseGcode(self, file, isVerbose: bool = False):
        pass

    def sendGcode(self, gcode: Buffer, isVerbose: bool = False):
        pass

    def home(self, isVerbose: bool = False):
        pass