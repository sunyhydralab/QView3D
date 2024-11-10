import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS

class Ports:
    @staticmethod
    def getPorts() -> list[ListPortInfo | SysFS]:
        """Get a list of all connected serial ports."""
        return serial.tools.list_ports.comports()

    @staticmethod
    def getPortByName(name: str) -> ListPortInfo | SysFS | None:
        """Get a specific port by its device name."""
        assert isinstance(name, str)
        ports = Ports.getPorts()
        for port in ports:
            if port.device == name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str) -> ListPortInfo | SysFS | None:
        """Get a specific port by its hardware ID."""
        assert isinstance(hwid, str)
        ports = Ports.getPorts()
        for port in ports:
            if hwid in port.hwid:
                return port
        return None