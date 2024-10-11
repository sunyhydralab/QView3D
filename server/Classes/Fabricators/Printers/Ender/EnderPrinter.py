from abc import ABCMeta
from typing import Callable
from typing_extensions import Buffer
from Classes.Fabricators.Device import Device
from Classes.Vector3 import Vector3
from Mixins.canPause import canPause
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes, checkOK, alwaysTrue
from Mixins.usesMarlinGcode import usesMarlinGcode


class EnderPrinter(Device, canPause, hasEndingSequence, hasResponsecodes, usesMarlinGcode, metaclass=ABCMeta):
    VENDORID = 0x1A86
    homePosition = Vector3(-3.0,-10.0,0.0)

    def connect(self):
        return usesMarlinGcode.connect(self)

    def disconnect(self):
        return usesMarlinGcode.disconnect(self)

    def endSequence(self):
        self.sendGcode(b"G91\n", alwaysTrue) # Relative positioning
        self.sendGcode(b"G1 E-2 F2700\n", alwaysTrue) # Retract a bit
        self.sendGcode(b"G1 E-2 Z0.2 F2400\n", alwaysTrue) # Retract and raise Z
        self.sendGcode(b"G1 X5 Y5 F3000\n", alwaysTrue) # Wipe out
        self.sendGcode(b"G1 Z10\n", alwaysTrue) # Raise Z more
        self.sendGcode(b"G90\n", alwaysTrue) # Absolute positioning
        self.sendGcode(b"G1 X0 Y220\n", alwaysTrue) # Present print
        self.sendGcode(b"M106 S0\n", alwaysTrue) # Turn-off fan
        self.sendGcode(b"M104 S0\n", alwaysTrue) # Turn-off hotend
        self.sendGcode(b"M140 S0\n", alwaysTrue) # Turn-off bed
        self.sendGcode(b"M84 X Y E\n", alwaysTrue) # Disable all steppers but Z

    def goTo(self, loc: Vector3):
        return usesMarlinGcode.goTo(self, loc)

    def pause(self):
        self.sendGcode(usesMarlinGcode.pause, checkOK)

    def resume(self):
        self.sendGcode(usesMarlinGcode.resume, checkOK)

    def getPrintTime(self):
        pass

    def getPrintHeadLocation(self) -> Vector3:
        return usesMarlinGcode.getPrintHeadLocation(self)

    def parseGcode(self, file):
        usesMarlinGcode.parseGcode(self, file)

    def sendGcode(self, gcode: Buffer, checkFunction: Callable):
        usesMarlinGcode.sendGcode(self, gcode, checkFunction)

    def home(self):
        return usesMarlinGcode.home(self)