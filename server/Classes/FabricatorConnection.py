import asyncio
import threading
from abc import ABC, abstractmethod
import uuid
import serial
from flask_socketio import SocketIO
from queue import Queue, Empty
import random


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

class SocketConnection:
    def __init__(self, websocket_connections, fabricator_id: str):
        """
        Initialize a websocket-based connection for a 3D printer with optional mock response generation.
        
        :param websocket_connections: Dictionary of websocket connections
        :param fabricator_id: Unique identifier for the printer
        :param timeout: Maximum time to wait for a response (default: 10.0)
        """
        self._fabricator_id = fabricator_id
        self._timeout = 10.0
        
        # Queue for storing incoming messages
        self._receive_queue = Queue()
        
        # Connection state
        self._is_open = True
        
        # Event for synchronizing responses
        self._response_event = threading.Event()
        
        # WebSocket connection management
        self._websocket_connections = websocket_connections
        self._websocket = None
        
        # Setup connection listeners
        self._setup_listeners()

    def _setup_listeners(self):
        """Configure websocket event listeners for receiving printer responses."""
        pass  # Listeners will be managed when sending/receiving messages through websockets.

    def write(self, data):
        """
        Send data to the printer via websocket, with optional mock response.
        
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
        self._websocket = self._websocket_connections.get(self._fabricator_id)
        
        if self._websocket is None:
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