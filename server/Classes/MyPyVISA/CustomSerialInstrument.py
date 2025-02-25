from pyvisa.resources import SerialInstrument
from pyvisa import constants
import re
from serial.tools.list_ports import grep


class CustomSerialInstrument(SerialInstrument):
    baud_rate: int = 115200
    comm_port: str | None = None
    def __init__(self, resource_manager, resource_name, **kwargs):
        """Extend SerialInstrument to include VID, PID, and serial number."""
        super().__init__(resource_manager, resource_name)
        self.comm_port = re.sub(r"ASRL", "COM", re.sub(r"::INSTR", "", resource_name))
        pyserial_port = next((dev for dev in grep(self.comm_port)), None)
        self._vid = pyserial_port.vid if pyserial_port else None
        self._pid = pyserial_port.pid if pyserial_port else None
        self._serial_number = pyserial_port.serial_number if pyserial_port else ""
        self._hwid = f"USB VID:PID={self.vid:04X}:{self.pid:04X} SER={self.serial_number}" if self.vid and self.pid else None
        self.baud_rate = kwargs.get("baud_rate", 115200)
        self._timeout = kwargs.get("open_timeout", 60000)
        self.open(kwargs.get("access_mode", constants.AccessModes.no_lock), kwargs.get("open_timeout", 60000))
        self.write_termination = '\n'
        self.read_termination = '\n'
        self.timeout = self._timeout
        self.write("M155 S1")


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
        return super().open(access_mode, open_timeout)

    def close(self) -> None:
        """Close the serial connection."""
        if self.is_open:
            self.write("M155 S0")
        return super().close()

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
        except AttributeError:
            return False