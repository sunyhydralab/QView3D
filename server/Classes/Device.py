from abc import ABC, abstractmethod

from flask import jsonify
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS

from Classes.PrinterList import PrinterList
from Classes.Printers.Ender.Ender3Pro import Ender3Pro
from Classes.Printers.Ender.Ender3 import Ender3
from Classes.Printers.Ender.EnderPrinter import EnderPrinter
from Classes.Printers.Prusa.PrusaMK3 import PrusaMK3
from Classes.Printers.Prusa.PrusaMK4 import PrusaMK4
from Classes.Printers.Prusa.PrusaMK4S import PrusaMK4S
from Classes.Printers.Prusa.PrusaPrinter import PrusaPrinter
from Classes.Vector3 import Vector3
import serial
import serial.tools.list_ports

class Device(ABC):
    # static variables
    __MODEL: str | None = None
    __VENDORID: int | None = None
    __PRODUCTID: int | None = None
    __DESCRIPTION: str | None = None
    __serialID: str | None = None
    __serialConnection: serial.Serial | None = None
    __serialPort: ListPortInfo | SysFS | None = None
    __homePosition: Vector3| None = None

    def __init__(self, serialPort: ListPortInfo | SysFS):
        self.__serialPort = serialPort
        self.__serialID = serialPort.serial_number

    @staticmethod
    def createDevice(serialPort: ListPortInfo | SysFS | None):
        """creates the correct printer object based on the serial port info"""
        if serialPort is None:
            return None
        if serialPort.vid == PrusaPrinter.__VENDORID:
            if serialPort.pid == PrusaMK4.__PRODUCTID:
                return PrusaMK4(serialPort)
            elif serialPort.pid == PrusaMK4S.__PRODUCTID:
                return PrusaMK4S(serialPort)
            elif serialPort.pid == PrusaMK3.__PRODUCTID:
                return PrusaMK3(serialPort)
            else:
                return None
        elif serialPort.vid == EnderPrinter.__VENDORID:
            if serialPort.pid == Ender3.__PRODUCTID:
                return Ender3(serialPort)
            elif serialPort.pid == Ender3Pro.__PRODUCTID:
                return Ender3Pro(serialPort)


    def connect(self):
        try:
            self.__serialConnection = serial.Serial(self.__serialPort.device, 115200, timeout=10)
            return True
        except Exception as e:
            # let the printer parent class deal with the error
            return e

    def disconnect(self):
        if self.__serialConnection:
            self.__serialConnection.close()
            self.__serialConnection = None

    @abstractmethod
    def home(self):
        pass

    @abstractmethod
    def diagnose(self):
        try:
            diagnoseString = ""
            for port in serial.tools.list_ports.comports():
                if port.device == self.__serialPort.device:
                    diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
                    hwid = self.getHWID().split(' LOCATION=')[0]
                    printerExists = PrinterList.getPrinterByHwid(hwid)
                    if printerExists:
                        printer = PrinterList.getPrinterByHwid(hwid)
                        diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {printer.name} <br> <b>Device:</b> {printer.device}, <br> <b>Description:</b> {printer.description}, <br><b> HWID:</b> {printer.hwid}"
            if diagnoseString == "":
                diagnoseString = "The port this printer is registered under is <b>not found</b>. Please check the connection and try again."
            # return diagnoseString
            return {
                "success": True,
                "message": "Printer successfully diagnosed.",
                "diagnoseString": diagnoseString,
            }

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500

    @abstractmethod
    def parseGcode(self):
        pass

    @abstractmethod
    def sendGcode(self, gcode: str):
        pass

    @abstractmethod
    def repair(self):
        pass

    @abstractmethod
    def hardReset(self):
        pass

    @abstractmethod
    def changeColor(self):
        pass

    def getModel(self):
        return self.__MODEL

    def getHWID(self):
        return self.__serialPort.hwid.split(' LOCATION=')[0]

    def getSerialConnection(self):
        return self.__serialConnection

    def getSerialPort(self):
        return self.__serialPort

    def getDescription(self):
        return self.__DESCRIPTION