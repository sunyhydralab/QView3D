from abc import ABCMeta
from Classes.Fabricators.Device import Device
from Mixins.hasEndingSequence import hasEndingSequence

class EnderPrinter(Device, hasEndingSequence, metaclass=ABCMeta):
    VENDORID = 0x1A86

    def endSequence(self):
        self.gcodeEnding("G91") # Relative positioning
        self.gcodeEnding("G1 E-2 F2700") # Retract a bit
        self.gcodeEnding("G1 E-2 Z0.2 F2400") # Retract and raise Z
        self.gcodeEnding("G1 X5 Y5 F3000") # Wipe out
        self.gcodeEnding("G1 Z10") # Raise Z more
        self.gcodeEnding("G90") # Absolute positioning
        self.gcodeEnding("G1 X0 Y220") # Present print
        self.gcodeEnding("M106 S0") # Turn-off fan
        self.gcodeEnding("M104 S0") # Turn-off hotend
        self.gcodeEnding("M140 S0") # Turn-off bed
        self.gcodeEnding("M84 X Y E") # Disable all steppers but Z


    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is EnderPrinter:
            if any("Ender" in B.__dict__.get('__DESCRIPTION__', '') for B in subclass.__mro__):
                return True
        return NotImplemented