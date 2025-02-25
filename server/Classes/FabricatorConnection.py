import asyncio
import re
import threading
import uuid
import json
from queue import Queue, Empty
from abc import ABC
from serial.tools.list_ports_common import ListPortInfo
from globals import current_app as app
from pyvisa.resources.resource import Resource


class FabricatorConnection(ABC):
    @staticmethod
    def staticCreateConnection(port: str = None, baud_rate: int = 115200, timeout: float = 10.0, websocket_connections: dict = None, fabricator_id: str = None):
        """
        Create a new connection to a 3D printer.
        :param str port: Serial port to connect to
        :param int baud_rate: Baud rate for the serial connection (default: 115200)
        :param float timeout: Maximum time to wait for a response (default: 10.0)
        :param dict websocket_connections: Dictionary of websocket connections
        :param str fabricator_id: Unique identifier for the printer
        :return: FabricatorConnection instance
        :rtype: Resource | SocketConnection
        """
        if websocket_connections is not None and fabricator_id is not None:
            return SocketConnection(port, baud_rate, websocket_connections, fabricator_id, timeout=timeout)
        elif port is not None and baud_rate is not None:
            if re.match(r"COM\d+", port):
                port = f"ASRL{re.sub(r"COM", "", port)}::INSTR"
            elif re.match(r"TCPIP\d+", port):
                ip = re.match(r"(\d+\.\d+\.\d+\.\d+)", port).group(1)
                port = f"TCPIP::{ip}::INSTR"
            if app.resource_manager.list_opened_resources():
                resource = next((resource for resource in app.resource_manager.list_opened_resources() if resource.resource_name == port), None)
                if resource: return resource
            return app.resource_manager.open_resource(port, baud_rate=baud_rate, timeout=timeout)
        else:
            raise ValueError("Invalid connection parameters")


class SocketConnection(FabricatorConnection):
    def __init__(self, port: str, baudrate: int, websocket_connection, fabricator_id: str , timeout: float = 10.0):
        """
        Initialize a websocket-based connection for a 3D printer with optional mock response generation.
        :param str port: Serial port to connect to
        :param int baudrate: Baudrate for the serial connection
        :param websocket_connection: the websocket connection
        :param str fabricator_id: Unique identifier for the printer
        :param float timeout: Maximum time to wait for a response (default: 10)
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
        gcode = data.decode('utf-8').strip() if isinstance(data, bytes) else str(data).strip()
        
        print(f"Sending G-code command: {gcode}")

        # Emit the G-code command
        self._send_message("send_gcode", {
            "printerid": self._fabricator_id, 
            "gcode": gcode
        })

    def read(self):
        """
        Read response from the printer.

        :return: Response from the printer as bytes
        """
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")

        # Use a local event and queue for this specific read operation

        async def on_message_received(client_id, message):
            try:
                data = json.loads(message)

                if data.get("event") != ("gcode_response"):
                    return

                info: dict = json.loads(data.get("data"))

                # if data.get("printerid") == self._fabricator_id:
                response = info.get("response", "")
                self._receive_queue.put(response)
                self._response_event.set()
                # else:
                #     print(f"Received message from unknown printer {data.get('printerid')}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode message: {message} - {e}")
            except Exception as e:
                print(f"Error in message handling: {e}")

        #try:
            # Register the temporary listener
        app.event_emitter.on("message_received", on_message_received)

        try:
            response = self._receive_queue.get(timeout=self._timeout)
            return response.encode('utf-8') if response else b''  # Convert string to bytes
        except Empty:
            return b''
        finally:
            # Unregister the listener to prevent memory leaks
            app.event_emitter.remove_event("message_received")

    def close(self):
        """
        Close the websocket connection.
        """
        if self._is_open:
            # Emit a disconnect event if needed
            self._send_message("printer_disconnect", {"printerid": self._fabricator_id})
            self._is_open = False
            if self._websocket_connection:
                asyncio.run(self._websocket_connection.close())  # Ensure closing the websocket.

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
        response = self.read()
        if response is None:
            response = b''

        return response

    @property
    def is_open(self):
        """
        Check if the connection is open.
        
        :return: Connection status
        """
        return self._is_open

    def _send_message(self, event, data):
        """Helper to send messages via the WebSocket connection."""
        if self._websocket_connection and self._is_open:
            message = {"event": event, "data": data}
            asyncio.run(self._websocket_connection.send(str(message)))
        else:
            print(f"Cannot send message: WebSocket connection is not open or not available.")

class EmuListPortInfo(ListPortInfo):
    def __init__(self, device: str, description: str = None, hwid: str = None):
        super().__init__(device)
        self._device = device
        self._description = description
        self._hwid = hwid
        self.vid = int(hwid.split("PID=")[1].split(":")[0], 16) if hwid else None
        self.pid = int(hwid.split(":")[2].split(" ")[0], 16) if hwid else None

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