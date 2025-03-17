from pyvisa.resources import SerialInstrument
from pyvisa.errors import InvalidSession
from pyvisa import constants
import re
from serial.tools.list_ports import grep
from globals import system_device_prefix, TemporaryTimeout

class CustomSerialInstrument(SerialInstrument):
    baud_rate: int = 115200

    def __init__(self, resource_manager, resource_name, **kwargs):
        """Extend SerialInstrument to include VID, PID, and serial number."""
        super().__init__(resource_manager, resource_name)
        self._comm_port = re.sub(r"ASRL", system_device_prefix, re.sub(r"::INSTR", "", resource_name))
        pyserial_port = next((dev for dev in grep(self.comm_port)), None)
        self._vid = getattr(pyserial_port, "vid") if pyserial_port else None
        self._pid = getattr(pyserial_port, "pid") if pyserial_port else None
        self._serial_number = getattr(pyserial_port, "serial_number") if pyserial_port else ""
        self._hwid = f"USB VID:PID={self.vid:04X}:{self.pid:04X} SER={self.serial_number}" if self.vid and self.pid else None
        self.baud_rate_no_session = kwargs.get("baud_rate", 115200)
        self.open_timeout = kwargs.get("open_timeout", 60000)
        self.timeout_no_session = kwargs.get("timeout", 60000)
        self.resource_name_no_session = resource_name

    def __str__(self):
        return f"{self.resource_name} ({self.hwid})"

    def __repr__(self):
        return self.__str__()


    def get_device_info(self):
        """Return device identification details."""
        return {
            "resource_name": self.resource_name,
            "VID": self.vid or None,
            "PID": self.pid or None,
            "Serial Number": self.serial_number or None,
        }

    def open(self, access_mode: constants.AccessModes = constants.AccessModes.no_lock, open_timeout: int = 5000):
        """Open the serial connection."""
        if self.is_open:
            self.write("M155 S1")
            return
        super().open(access_mode, open_timeout)
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.timeout = getattr(self,"timeout_no_session")
        self.write("M155 S1")

    def close(self) -> None:
        """Close the serial connection."""
        if self.is_open:
            self.write("M155 S100")
            self.write("M155 S0")
            super().close()
        assert not self.is_open, "Port did not close properly"

    def write(self, message: str, termination: str | None = None, encoding: str | None = None):
        if re.match(r"M109|M190", message):
            with TemporaryTimeout(self, None):
                super().write(message, termination, encoding)
        else:
            super().write(message, termination, encoding)

    @property
    def hwid(self):
        return self._hwid

    @hwid.setter
    def hwid(self, hwid):
        self._hwid = f"USB VID:PID={self.vid:04X}:{self.pid:04X} SER={self.serial_number}" if (self.vid and self.pid) else None

    @property
    def vid(self):
        return self._vid

    @vid.setter
    def vid(self, vid: int):
        self._vid = vid

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, pid: int):
        self._pid = pid

    @property
    def serial_number(self):
        return self._serial_number

    @serial_number.setter
    def serial_number(self, serial_number):
        self._serial_number = serial_number

    @property
    def comm_port(self):
        return self._comm_port

    @property
    def is_open(self):
        try:
            return self.session is not None
        except InvalidSession:
            return False