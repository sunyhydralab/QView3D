import asyncio
import threading
from abc import ABC
import uuid
import serial
from queue import Queue, Empty

from serial.tools.list_ports_common import ListPortInfo


class FabricatorConnection(ABC):
    @staticmethod
    def staticCreateConnection(port: str = None, baudrate: int = None, timeout: float = 10.0, websocket_connections: dict = None, fabricator_id: str = None):
        """Create a new connection to a 3D printer."""
        if websocket_connections is not None and fabricator_id is not None:
            return SocketConnection(websocket_connections, fabricator_id)
        elif port is not None and baudrate is not None:
            return SerialConnection(port, baudrate, timeout=timeout)
        else:
            raise ValueError("Invalid connection parameters")

class SerialConnection(FabricatorConnection, serial.Serial):
    def __init__(self, port: str, baudrate: int, timeout: float):
        super().__init__(port, baudrate, timeout=timeout)


class SocketConnection(FabricatorConnection):
    def __init__(self, port: str, baudrate: int, timeout: float, websocket_connection, fabricator_id: str):
        """
        Initialize a websocket-based connection for a 3D printer with optional mock response generation.
        
        :param websocket_connection: Dictionary of websocket connections
        :param fabricator_id: Unique identifier for the printer
        :param timeout: Maximum time to wait for a response (default: 10.0)
        """
        self._fabricator_id = fabricator_id
        self._timeout = timeout

        # Queue for storing incoming messages
        self._receive_queue = Queue()

        # Connection state
        self._is_open = True

        # Event for synchronizing responses
        self._response_event = threading.Event()

        # WebSocket connection management
        self._websocket_connection = websocket_connection

        # Setup connection listeners
        self._setup_listeners()

        self.emuListPortInfo = EmuListPortInfo(device=port, description="Emulator", hwid="")

        self.port = self.emuListPortInfo.device
        self.baudrate = baudrate
        self.timeout = timeout

    def _setup_listeners(self):
        """Configure websocket event listeners for receiving printer responses."""
        pass  # Listeners will be managed when sending/receiving messages through websockets.

    def write(self, data):
        """
        Send data to the printer via websocket.
        
        :param data: Data to be sent (typically G-code)
        """
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")
        
        # Clear any previous responses
        self._response_event.clear()
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
            except Empty:
                break
        
        # Convert data to string if it's bytes
        gcode = data.decode('utf-8') if isinstance(data, bytes) else data
        
        # Emit the G-code command
        self._send_message("send_gcode", {
            "printerid": self._fabricator_id, 
            "gcode": gcode
        })

    def read(self):
        """
        Read response from the printer.
        
        :return: Response from the printer
        """
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")
        
        # Wait for response with timeout
        if not self._response_event.wait(timeout=self._timeout):
            raise TimeoutError(f"No response received within {self._timeout} seconds")
        
        try:
            return self._receive_queue.get(block=False)
        except Empty:
            return ""

    def close(self):
        """
        Close the websocket connection.
        """
        if self._is_open:
            # Emit a disconnect event if needed
            self._send_message("printer_disconnect", {"printerid": self._fabricator_id})
            self._is_open = False
            if self._websocket:
                asyncio.run(self._websocket.close())  # Ensure closing the websocket.

    def open(self):
        """
        Open the websocket connection.
        """
        # Generate unique WebSocket connection ID
        websocket_id = str(uuid.uuid4())
        
        # Find the appropriate websocket based on fabricator_id
        if self._websocket_connection is None:
            raise ConnectionError(f"WebSocket not found for printer {self._fabricator_id}")
        
        # Emit a connection/handshake event via WebSocket
        self._send_message("printer_connect", {"printerid": self._fabricator_id})
        
        # Wait for connection confirmation
        connection_confirmed = self._response_event.wait(timeout=self._timeout)
        if connection_confirmed:
            self._is_open = True
        else:
            raise ConnectionError(f"Could not establish websocket connection for printer {self._fabricator_id}")

    def reset_input_buffer(self):
        """
        Clear the input buffer.
        """
        # Clear the receive queue
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
            except Empty:
                break
        
        # Clear any pending response events
        self._response_event.clear()

    def readline(self):
        """
        Read a line of response from the printer.
        
        :return: A single line of response
        """
        return self.read()

    @property
    def is_open(self):
        """
        Check if the connection is open.
        
        :return: Connection status
        """
        return self._is_open

    def _send_message(self, event, data):
        """Helper to send messages via the WebSocket connection."""
        if self._websocket and self._is_open:
            message = {"event": event, "data": data}
            asyncio.run(self._websocket.send(str(message)))
        else:
            print(f"Cannot send message: WebSocket connection is not open or not available.")

class EmuListPortInfo(ListPortInfo):
    def __init__(self, device: str, description: str = None, hwid: str = None):
        super().__init__(device)
        self._device = device
        self._description = description
        self._hwid = hwid

    def __repr__(self):
        return f"EmuListPortInfo(device={self.device}, description={self.description}, hwid={self.hwid})"

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def hwid(self):
        return self._hwid

    @hwid.setter
    def hwid(self, value):
        self._hwid = value
