import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS


class Ports:
    @staticmethod
    def getPorts():
        return serial.tools.list_ports.comports()

    @staticmethod
    def getPortByName(name: str) -> ListPortInfo | SysFS | None:
        ports = Ports.getPorts()
        for port in ports:
            if port.device == name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str) -> ListPortInfo | SysFS | None:
        ports = Ports.getPorts()
        for port in ports:
            if port.hwid == hwid:
                return port
        return None