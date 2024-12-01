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

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def reset_input_buffer(self):
        pass

    @abstractmethod
    def readline(self):
        pass

class SerialConnection(FabricatorConnection):
    def __init__(self, port: str, baudrate: int, timeout: float):
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        self.is_open = self.serial.is_open

    def write(self, data):
        self.serial.write(data)

    def read(self):
        return self.serial.readline()
    
    def close(self):
        self.serial.close()
    
    def reset_input_buffer(self):
        self.serial.reset_input_buffer()
    
    def readline(self):
        return self.serial.readline()
    
    @property
    def is_open(self):
        return self.serial.is_open

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
    
    def close(self):
        # TODO: make this!!
        pass

    def reset_input_buffer(self):
        # TODO: make this!!
        pass

    def readline(self):
        # TODO: make this!!
        return ""

    @property
    def is_open(self):
        return self.is_open
