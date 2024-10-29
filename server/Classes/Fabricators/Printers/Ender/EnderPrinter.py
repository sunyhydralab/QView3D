from abc import ABCMeta
from typing import Callable
from typing_extensions import Buffer
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes, alwaysTrue
from Mixins.usesMarlinGcode import usesMarlinGcode


class EnderPrinter(Printer, hasEndingSequence, usesMarlinGcode, metaclass=ABCMeta):
    VENDORID = 0x1A86
    homePosition = Vector3(-3.0,-10.0,0.0)

    def connect(self):
        return usesMarlinGcode.connect(self)

    def disconnect(self):
        return usesMarlinGcode.disconnect(self)

    def endSequence(self):
        self.sendGcode(b"G91\n")  # Relative positioning
        self.sendGcode(b"G1 E-2 F2700\n")  # Retract a bit
        self.sendGcode(b"G1 E-2 Z0.2 F2400\n")  # Retract and raise Z
        self.sendGcode(b"G1 X5 Y5 F3000\n")  # Wipe out
        self.sendGcode(b"G1 Z10\n")  # Raise Z more
        self.sendGcode(b"G90\n")  # Absolute positioning
        self.sendGcode(b"G1 X0 Y220\n")  # Present print
        self.sendGcode(b"M106 S0\n")  # Turn-off fan
        self.sendGcode(b"M104 S0\n")  # Turn-off hotend
        self.sendGcode(b"M140 S0\n")  # Turn-off bed
        self.sendGcode(b"M84 X Y E\n")  # Disable all steppers but Z

    def goTo(self, loc: Vector3, isVerbose: bool = False):
        return usesMarlinGcode.goTo(self, loc, isVerbose)

    def getPrintTime(self):
        pass

    def getToolHeadLocation(self) -> Vector3:
        return usesMarlinGcode.getToolHeadLocation(self)

    def parseGcode(self, file, isVerbose: bool = False):
        return usesMarlinGcode.parseGcode(self, file, isVerbose)

    def sendGcode(self, gcode: Buffer, isVerbose: bool = False):
        usesMarlinGcode.sendGcode(self, gcode, isVerbose)

    def home(self, isVerbose: bool = False):
        return usesMarlinGcode.home(self, isVerbose)