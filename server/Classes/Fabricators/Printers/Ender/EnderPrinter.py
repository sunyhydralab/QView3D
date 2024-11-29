from abc import ABCMeta
from time import sleep
from Classes.Fabricators.Printers.Printer import Printer
from Classes.Vector3 import Vector3
from Mixins.hasEndingSequence import hasEndingSequence


class EnderPrinter(Printer, hasEndingSequence, metaclass=ABCMeta):
    VENDORID = 0x1A86
    homePosition = Vector3(-3.0,-10.0,0.0)

    def connect(self):
        ret = super().connect()
        sleep(7)
        return ret

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

    def getPrintTime(self):
        pass