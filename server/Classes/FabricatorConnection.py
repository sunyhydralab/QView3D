import threading
from abc import ABC
import uuid
import serial
from queue import Queue, Empty
import json
from serial.tools.list_ports_common import ListPortInfo
from services.app_service import current_app


class FabricatorConnection(ABC):
    @staticmethod
    def staticCreateConnection(port: str = None, baudrate: int = 115200, timeout: float = 10.0, websocket_connections: dict = None, fabricator_id: str = None):
        """
        Create a new connection to a 3D printer.
        :param str port: Serial port to connect to
        :param int baudrate: Baudrate for the serial connection (default: 115200)
        :param float timeout: Maximum time to wait for a response (default: 10.0)
        :param dict websocket_connections: Dictionary of websocket connections
        :param str fabricator_id: Unique identifier for the printer
        :return: FabricatorConnection instance
        :rtype: SerialConnection | SocketConnection
        """
        if websocket_connections is not None and fabricator_id is not None:
            return SocketConnection(port, baudrate, websocket_connections, fabricator_id, timeout=timeout)
        elif port is not None and baudrate is not None:
            return SerialConnection(port, baudrate, timeout=timeout)
        else:
            raise ValueError("Invalid connection parameters")

class SerialConnection(FabricatorConnection, serial.Serial):
    def __init__(self, port: str, baudrate: int, timeout: float):
        # TODO: undo temp fix and make sure that queryAll doesnt try to re-instantiate the serial connection.
        try:
            super().__init__(port, baudrate, timeout=timeout)
        except serial.SerialException as e:
            if not "Access is denied" in str(e):
                print(f"Failed to open serial connection: {e}")
                raise ConnectionError(f"Failed to open serial connection: {e}")


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

        # Store last response
        self._last_response = None

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

        def on_message_received(client_id, message):
            try:
                data = json.loads(message)

                
                event_type = data.get("event", "unknown")
                info = data.get("data", {})
                
                # Handle different data formats
                if isinstance(info, str):
                    try:
                        parsed_info = json.loads(info)
                        response = parsed_info.get("response", info)
                    except json.JSONDecodeError:
                        response = info
                elif isinstance(info, dict):
                    response = info.get("response", str(info))
                else:
                    response = str(info)
                    
                # Log ALL events and process ALL of them
                print(f"Received event: {event_type}, response: {response}")
                self._receive_queue.put(response)
                self._response_event.set()
                
            except json.JSONDecodeError as e:
                print(f"Failed to decode message: {message} - {e}")
            except Exception as e:
                print(f"Error in message handling: {e}")
                

        try:
            from services.app_service import current_app
            current_app.event_emitter.on("message_received", on_message_received)

            response = self._receive_queue.get(timeout=1.0)
            self._last_response = response.encode('utf-8') if isinstance(response, str) else response
            return self._last_response
        except Empty:
            # Return the last actual response we received, or default if none yet
            if self._last_response is not None:
                print(f"No new response, returning last response: {self._last_response}")
                return self._last_response
            else:
                print("No responses received yet, returning default 'ok'")
                return b"ok\n"
        finally:
            # Unregister the listener to prevent memory leaks
            from services.app_service import current_app
            current_app.event_emitter.remove_event("message_received")

    def close(self):
        """
        Close the websocket connection.
        """
        if self._is_open:
            self._send_message("printer_disconnect", {"printerid": self._fabricator_id})
            self._is_open = False
            print(f"Closed connection for printer {self._fabricator_id}")

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
        """Helper to send messages via SocketIO (non-blocking)."""
        try:
            from services.app_service import current_app
            current_app.socketio.emit('fabricator_command', {
                'event': event,
                'data': data,
                'fabricator_id': self._fabricator_id
            })
            print(f"Sent {event} via SocketIO for printer {self._fabricator_id}")
        except Exception as e:
            print(f"Failed to send message via SocketIO: {e}")
                  
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
