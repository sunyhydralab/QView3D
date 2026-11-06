import sys
from pathlib import Path
from types import SimpleNamespace


# Allow this test code to import files from QView3D/server
SERVER_DIR = Path(__file__).resolve().parents[1] / "server"

if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))


from Classes.Fabricators.Device import Device


class MockableDevice(Device):
    """
    Small Device used only for hardware-free testing.

    It behaves like a QView3D Device, but we control
    what serial connection it uses.
    """

    MODEL = "Mock Printer"
    DESCRIPTION = "Mock Printer"
    MAXFEEDRATE = 12000

    def __init__(self, connection=None):
        self.dbID = 999
        self.name = self.DESCRIPTION

        # Fake serial-port information.
        self.serialPort = SimpleNamespace(
            device="MOCK_PORT",
            serial_number="MOCK_SERIAL"
        )

        self.serialID = self.serialPort.serial_number

        # This can be a MagicMock or FakeSerialConnection.
        self.serialConnection = connection

        self.logger = None
        self.status = "idle"
        self.verdict = ""
        self.websocket_connection = None


class FakeSerialConnection:
    """
    Simple replacement for a real serial connection.

    Instead of talking to a USB printer, this object
    stores commands and returns fake printer responses.
    """

    def __init__(self, responses=None):
        self.is_open = True
        self.port = "MOCK_PORT"
        self.baudrate = 115200
        self.timeout = 1

        self.writes = []

        if responses is None:
            responses = [b"ok\n"]

        self.responses = list(responses)

    def write(self, data):
        """Pretend to send data to the printer."""
        self.writes.append(data)
        return len(data)

    def readline(self):
        """Pretend to receive a response from the printer."""
        if self.responses:
            return self.responses.pop(0)

        return b"ok\n"

    def reset_input_buffer(self):
        """Pretend to clear the printer's input buffer."""
        pass

    def close(self):
        """Pretend to close the serial connection."""
        self.is_open = False