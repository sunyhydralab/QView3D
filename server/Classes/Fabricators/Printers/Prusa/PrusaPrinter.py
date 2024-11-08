from abc import ABCMeta, abstractmethod
from typing_extensions import Buffer
from Classes.Vector3 import Vector3
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.gcode.usesMarlinGcode import usesMarlinGcode


class PrusaPrinter(Printer, hasEndingSequence, usesMarlinGcode, metaclass=ABCMeta):
    VENDORID = 0x2C99


    def sendGcode(self, gcode: Buffer, isVerbose: bool = False):
        return usesMarlinGcode.sendGcode(self, gcode, isVerbose)

    def parseGcode(self, file, isVerbose=False):
        return usesMarlinGcode.parseGcode(self, file, isVerbose)

    def connect(self):
        return usesMarlinGcode.connect(self)

    def disconnect(self):
        usesMarlinGcode.disconnect(self)

    def home(self, isVerbose: bool = False):
        return usesMarlinGcode.home(self, isVerbose)

    def goTo(self, loc: Vector3, isVerbose: bool = False):
        return usesMarlinGcode.goTo(self, loc, isVerbose)

    @abstractmethod
    def endSequence(self):
        pass

    @abstractmethod
    def getPrintTime(self):
        pass

    def getToolHeadLocation(self) -> Vector3:
        return usesMarlinGcode.getToolHeadLocation(self)