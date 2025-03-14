from Classes.Device_Classes import device_classes
from Classes.Fabricators.Device import Device
from typing import TextIO
from pyvisa.resources.resource import Resource
from globals import current_app

class DeviceFactory:
    def __new__(cls, serialPort: Resource | None, consoleLogger: TextIO | None = None, fileLogger: str | None = None, websocket_connection = None, dbID: int = 100000, name: str = "New Device", *args, **kwargs) -> Device:
        try:
            assert hasattr(serialPort, "vid"), "serial port has no VID"
            assert hasattr(serialPort, "pid"), "serial port has no PID"
            cls = device_classes.get((serialPort.vid, serialPort.pid), None)
            assert cls is not None, f"Device not found for VID: {serialPort.vid}, PID: {serialPort.pid}"
            return cls(dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, websocket_connection=websocket_connection, addLogger=True, name=name)
        except Exception as e:
            current_app.handle_errors_and_logging(e, consoleLogger)
            # TODO: figure out how to handle misses gracefully
            return None
