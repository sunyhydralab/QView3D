from abc import ABCMeta
from typing_extensions import Buffer, Callable
from Classes.Vector3 import Vector3
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.canPause import canPause
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes, checkXYZ, checkOK
from Mixins.usesMarlinGcode import usesMarlinGcode


class PrusaPrinter(Printer, canPause, hasEndingSequence, hasResponsecodes, usesMarlinGcode, metaclass=ABCMeta):
    VENDORID = 0x2C99


    def sendGcode(self, gcode: Buffer, checkFunction: Callable):
        return usesMarlinGcode.sendGcode(self, gcode, checkFunction)

    def connect(self):
        return usesMarlinGcode.connect(self)

    def disconnect(self):
        usesMarlinGcode.disconnect(self)

    def home(self):
        return usesMarlinGcode.home(self)

    def goTo(self, loc: Vector3):
        return usesMarlinGcode.goTo(self, loc)

    def pause(self):
        self.sendGcode(usesMarlinGcode.pause, checkOK)

    def resume(self):
        self.sendGcode(usesMarlinGcode.resume, checkOK)

    def endSequence(self):
        pass

    def getPrintTime(self):
        pass

    def getPrintHeadLocation(self) -> Vector3:
        return usesMarlinGcode.getPrintHeadLocation(self)