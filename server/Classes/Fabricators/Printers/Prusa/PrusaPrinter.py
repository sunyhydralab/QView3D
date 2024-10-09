from abc import ABCMeta

from typing_extensions import Buffer

from Classes.Fabricators.Device import Device
from Classes.Vector3 import Vector3
from Classes.Fabricators.Printers.Printer import Printer
from Mixins.canPause import canPause
from Mixins.hasEndingSequence import hasEndingSequence
from Mixins.hasResponseCodes import hasResponsecodes, checkXYZ, checkOK
from Mixins.usesMarlinGcode import usesMarlinGcode


class PrusaPrinter(Printer, canPause, hasEndingSequence, hasResponsecodes, usesMarlinGcode, metaclass=ABCMeta):
    VENDORID = 0x2C99

    def sendGcode(self, gcode: Buffer, checkFunction):
        self.serialConnection.write(gcode)
        while self.serialConnection.readline() == b'ok\n':
            pass
        while True:
            try:
                line = self.serialConnection.readline()
                print(line)
                if checkFunction(line):
                    break
            except Exception as e:
                print(e)
                break


    def connect(self):
        Device.connect(self)
        try:
            if self.serialConnection:
                self.serialConnection.write(usesMarlinGcode.connect)
                return True
        except Exception as e:
            return e

    def disconnect(self):
        if self.serialConnection:
            self.serialConnection.write(usesMarlinGcode.disconnect)
            self.serialConnection.close()
            self.serialConnection = None

    def home(self):
        self.sendGcode(usesMarlinGcode.home, checkOK)
        return self.getHomePosition() == self.getPrintHeadLocation()

    def goTo(self, loc: Vector3):
        self.sendGcode(usesMarlinGcode.goTo(loc), checkXYZ)
        return loc == self.getPrintHeadLocation()

    def pause(self):
        self.sendGcode(usesMarlinGcode.pause, checkOK)

    def resume(self):
        self.sendGcode(usesMarlinGcode.resume, checkOK)

    def endSequence(self):
        pass

    def getPrintTime(self):
        pass

    def getPrintHeadLocation(self) -> Vector3:
        self.serialConnection.write("M114\n".encode("utf-8"))
        response = ""
        while not (("X:" in response) and ("Y:" in response) and ("Z:" in response)):
            response = self.serialConnection.readline()
            print(response)
            response = response.decode("utf-8")
        x = float(response.split("X:")[1].split(" ")[0])
        y = float(response.split("Y:")[1].split(" ")[0])
        z = float(response.split("Z:")[1].split(" ")[0])
        return Vector3(x,y,z)


    @classmethod
    def __subclasshook__(cls, subclass):
        if cls is PrusaPrinter:
            if any("Prusa" in B.__dict__.get('__DESCRIPTION__', '') for B in subclass.__mro__):
                return True
        return NotImplemented
