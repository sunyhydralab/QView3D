from abc import ABCMeta, abstractmethod
from typing_extensions import Buffer
from Classes.Vector3 import Vector3
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.gcode.usesPrusaGcode import usesPrusaGcode
from Mixins.hasEndingSequence import hasEndingSequence


class PrusaPrinter(Printer, hasEndingSequence, usesPrusaGcode, metaclass=ABCMeta):
    VENDORID = 0x2C99

    def sendGcode(self, gcode: Buffer, isVerbose: bool = False):
        return usesPrusaGcode.sendGcode(self, gcode, isVerbose)

    def parseGcode(self, file, isVerbose=False):
        return usesPrusaGcode.parseGcode(self, file, isVerbose)

    def connect(self):
        return usesPrusaGcode.connect(self)

    def disconnect(self):
        usesPrusaGcode.disconnect(self)

    def home(self, isVerbose: bool = False):
        return usesPrusaGcode.home(self, isVerbose)

    def goTo(self, loc: Vector3, isVerbose: bool = False):
        return usesPrusaGcode.goTo(self, loc, isVerbose)

    @abstractmethod
    def endSequence(self):
        pass

    @abstractmethod
    def getPrintTime(self):
        pass

    def getToolHeadLocation(self) -> Vector3:
        return usesPrusaGcode.getToolHeadLocation(self)