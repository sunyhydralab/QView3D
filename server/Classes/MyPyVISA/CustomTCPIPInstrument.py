from pyvisa.resources import TCPIPInstrument
from pyvisa import constants
from pyvisa.errors import InvalidSession
import re
class CustomTCPIPInstrument(TCPIPInstrument):
    def __init__(self, resource_manager, resource_name, **kwargs):
        super().__init__(resource_manager, resource_name)
        self.comm_port = re.sub(r"TCPIP\d+::", "", re.sub(r"::(INSTR|SOCKET)", "", resource_name))
        self._timeout = kwargs.get("open_timeout", 60000)
        self._vid = kwargs.get("vid", None)
        self._pid = kwargs.get("pid", None)
        self._serial_number = kwargs.get("serial_number", "")
        self._hwid = f"TCPIP VID:PID={self.vid:04X}:{self.pid:04X} SER={self.serial_number}" if self.vid and self.pid else None
        self.open(kwargs.get("access_mode", constants.AccessModes.no_lock), kwargs.get("open_timeout", 60000))
        self.timeout = self._timeout
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.write("M155 S1")

    def open(self, access_mode: constants.AccessModes = constants.AccessModes.no_lock, open_timeout: int = 5000):
        """Open the serial connection."""
        if self.is_open:
            return self
        return super().open(access_mode, open_timeout)

    def close(self) -> None:
        """Close the serial connection."""
        return super().close()

    def __str__(self):
        return f"{self.resource_name} ({self.hwid})"

    def __repr__(self):
        return self.__str__()

    @property
    def hwid(self):
        return self._hwid

    @property
    def vid(self):
        return self._vid

    @property
    def pid(self):
        return self._pid

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def is_open(self):
        try:
            return self.session is not None
        except InvalidSession:
            return False

class EmuTCPIPInstrument(CustomTCPIPInstrument):
    def __init__(self, resource_manager, resource_name, **kwargs):
        super().__init__(resource_manager, resource_name, **kwargs)
        if kwargs.get("hwid", False):
            self._hwid = kwargs.get("hwid")
            self._vid = self.hwid.split("VID:PID=")[1].split(":")[0]
            self._pid = self.hwid.split("VID:PID=")[1].split(":")[1].split(" ")[0]
            self._serial_number = self.hwid.split("SER=")[1]
        else:
            self._vid = kwargs.get("vid", 0x0403)
            self._pid = kwargs.get("pid", 0x6001)
            self._serial_number = kwargs.get("serial_number", "FT123456")
            self._hwid = f"TCPIP VID:PID={self.vid:04X}:{self.pid:04X} SER={self.serial_number}" if self.vid and self.pid else None
        self.open(kwargs.get("access_mode", constants.AccessModes.no_lock), kwargs.get("open_timeout", 60000))
        self.timeout = self._timeout
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.write("M155 S1")