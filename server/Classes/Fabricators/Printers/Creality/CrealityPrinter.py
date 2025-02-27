from abc import ABCMeta
from time import sleep
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from Mixins.hasEndingSequence import hasEndingSequence
from globals import VID


class EnderPrinter(Printer, hasEndingSequence, metaclass=ABCMeta):
    VENDORID = VID.CREALITY
    homePosition = Vector3(-3.0,-10.0,0.0)

    def connect(self):
        ret = super().connect()
        sleep(7)
        return ret

    def endSequence(self):
        self.sendGcode("G91")  # Relative positioning
        self.sendGcode("G1 E-2 F2700")  # Retract a bit
        self.sendGcode("G1 E-2 Z0.2 F2400")  # Retract and raise Z
        self.sendGcode("G1 X5 Y5 F3000")  # Wipe out
        self.sendGcode("G1 Z10")  # Raise Z more
        self.sendGcode("G90")  # Absolute positioning
        self.sendGcode("G1 X0 Y220")  # Present print
        self.sendGcode("M106 S0")  # Turn-off fan
        self.sendGcode("M104 S0")  # Turn-off hotend
        self.sendGcode("M140 S0")  # Turn-off bed
        self.sendGcode("M84 X Y E")  # Disable all steppers but Z

    def getPrintTime(self):
        pass