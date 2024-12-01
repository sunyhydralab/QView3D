from abc import ABC, abstractmethod

import serial
from flask_socketio import SocketIO


class FabricatorConnection(ABC):
    is_open = False

    @abstractmethod
    def write(self, data):
        pass

    @abstractmethod
    def read(self):
        pass

class SerialConnection(FabricatorConnection):
    def __init__(self, port: str, baudrate: int, timeout: float):
        self.is_open = False
        self.serial = serial.Serial(port, baudrate, timeout=timeout)

    def write(self, data):
        self.serial.write(data)

    def read(self):
        return self.serial.readline()

class SocketConnection(FabricatorConnection):
    def __init__(self, socketio: SocketIO, fabricator_id: str):
        self.is_open = False
        self.socketio = socketio
        self.fabricator_id = fabricator_id
        self.response = None

    def write(self, data):
        self.socketio.emit("send_gcode", {"printerid": self.fabricator_id, "gcode": data})

    def read(self):
        return self.response or ""
