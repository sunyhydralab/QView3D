from Classes.FabricatorConnection import FabricatorConnection
from Classes.Fabricators.Printers.Creality.Ender3 import Ender3
from Classes.Fabricators.Printers.Creality.Ender3Pro import Ender3Pro
from pyvisa.resources.resource import Resource
from typing import TextIO
from Classes.Fabricators.Device import Device

class Creality_Factory:
    def __new__(cls, serialPort: Resource | None, consoleLogger: TextIO | None = None, fileLogger: str | None = None, websocket_connection = None, dbID: int = 100000, name: str = "New Device", addLogger: bool = False, *args, **kwargs) -> Device:
        model = cls.getModelFromGcodeCommand(serialPort)
        if "Ender-3 Pro" in model:
            return Ender3Pro(dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
        elif "Ender-3" in model:
            return Ender3(dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
        else:
            # TODO: figure out how to handle misses gracefully.
            return None

    @staticmethod
    def getModelFromGcodeCommand(serialPort: Resource | None) -> str:
        """
        returns the model of the printer based on the response to M997, NOTE: this is meant for use with Ender printers only for now.
        :param Resource | None serialPort: the serial port to connect to
        :rtype: str
        """
        print(serialPort.resource_name)
        testName = FabricatorConnection.staticCreateConnection(port=str(serialPort.resource_name), baud_rate=115200,
                                                               timeout=60000)
        testName.write("M997")
        while True:
            response = testName.read()
            if "MACHINE_NAME" in response:
                testName.reset_input_buffer()
                testName.close()
                break
        return response