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
    def staticCreateConnection(port=None, baudrate=115200, timeout=10.0, websocket_connections=None, fabricator_id=None):
        if websocket_connections is not None and fabricator_id is not None:
            return SocketConnection(port, baudrate, websocket_connections, fabricator_id, timeout=timeout)
        elif port is not None and baudrate is not None:
            return SerialConnection(port, baudrate, timeout=timeout)
        else:
            raise ValueError("Invalid connection parameters")

class SerialConnection(FabricatorConnection, serial.Serial):
    def __init__(self, port, baudrate, timeout):
        try:
            super().__init__(port, baudrate, timeout=timeout, inter_byte_timeout=1.0)
        except serial.SerialException as e:
            if not "Access is denied" in str(e):
                print(f"Failed to open serial connection: {e}")
                raise ConnectionError(f"Failed to open serial connection: {e}")

class SocketConnection(FabricatorConnection):
    def __init__(self, port, baudrate, websocket_connection, fabricator_id, timeout=10.0):
        self._fabricator_id = fabricator_id
        self._timeout = timeout
        # Large buffer for streaming thousands of G-code commands
        self._receive_queue = Queue(maxsize=10000)
        self._line_buffer = []  # Buffer for multi-line responses
        self._last_response = None
        self._is_open = True
        self._response_event = threading.Event()
        self._websocket_connection = websocket_connection
        self._listener_registered = False
        self.emuListPortInfo = EmuListPortInfo(device=port, description="Emulator", hwid="")
        self.port = self.emuListPortInfo.device
        self.baudrate = baudrate
        self.timeout = timeout
        self._setup_listeners()

    def _setup_listeners(self):
        """Setup permanent listener for this connection"""
        listener_id = f"gcode_response_{self._fabricator_id}"

        def on_message_received(message):
            try:
                print(f"[SocketConnection] RAW MESSAGE RECEIVED: type={type(message)}, content={message[:200] if isinstance(message, (str, bytes)) else message}")
                data = json.loads(message) if isinstance(message, str) else message
                response = data.get("response", "ok")
                print(f"[SocketConnection] EXTRACTED RESPONSE for {self._fabricator_id}: '{response}' (len={len(response)})")
                # Add newline to match serial behavior
                if not response.endswith('\n'):
                    response += '\n'
                self._receive_queue.put(response)
                self._response_event.set()
            except json.JSONDecodeError as e:
                print(f"[SocketConnection] JSON DECODE ERROR: {message} - {e}")
            except Exception as e:
                print(f"[SocketConnection] ERROR in message handling: {e}")
                import traceback
                traceback.print_exc()

        # Register permanent listener
        current_app.event_emitter.on(listener_id, on_message_received)
        self._listener_registered = True
        print(f"[SocketConnection] Registered permanent listener: {listener_id}")

    def write(self, data):
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")
        self._response_event.clear()
        # Clear line buffer for new command
        self._line_buffer.clear()
        # Clear receive queue
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
            except Empty:
                break
        gcode = data.decode('utf-8').strip() if isinstance(data, bytes) else str(data).strip()
        print(f"Sending G-code command: {gcode}")
        self._send_message("send_gcode", {"printerid": self._fabricator_id, "gcode": gcode})

    def read(self):
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")

        try:
            # Wait for response from permanent listener
            response = self._receive_queue.get(timeout=self._timeout)
            self._last_response = response.encode('utf-8') if isinstance(response, str) else response
            print(f"[SocketConnection] read() returning: {self._last_response}")
            return self._last_response
        except Empty:
            # Timeout - return last response or default
            if self._last_response is not None:
                print(f"[SocketConnection] Timeout, returning last response: {self._last_response}")
                return self._last_response
            else:
                print("[SocketConnection] Timeout, returning default 'ok\\n'")
                return b"ok\n"

    def close(self):
        if self._is_open:
            self._send_message("printer_disconnect", {"printerid": self._fabricator_id})
            self._is_open = False
            # Clean up permanent listener
            if self._listener_registered:
                listener_id = f"gcode_response_{self._fabricator_id}"
                current_app.event_emitter.remove_event(listener_id)
                self._listener_registered = False
            print(f"Closed connection for printer {self._fabricator_id}")

    def open(self):
        if self._websocket_connection is None:
            raise ConnectionError(f"WebSocket not found for printer {self._fabricator_id}")
        self._send_message("printer_connect", {"printerid": self._fabricator_id})
        connection_confirmed = self._response_event.wait(timeout=self._timeout)
        if connection_confirmed:
            self._is_open = True
        else:
            raise ConnectionError(f"Could not establish websocket connection for printer {self._fabricator_id}")

    def reset_input_buffer(self):
        while not self._receive_queue.empty():
            try:
                self._receive_queue.get_nowait()
            except Empty:
                break
        self._response_event.clear()

    def readline(self):
        """Read a single line, buffering multi-line responses"""
        if not self._is_open:
            raise ConnectionError("WebSocket connection is not open")

        # If we have buffered lines, return the first one
        if self._line_buffer:
            line = self._line_buffer.pop(0)
            return line.encode('utf-8') if isinstance(line, str) else line

        # Otherwise, get a new response from the queue
        try:
            response = self._receive_queue.get(timeout=self._timeout)

            # Handle string responses
            if isinstance(response, str):
                # Split multi-line responses
                lines = response.split('\n')
                # Filter out empty lines but keep meaningful ones
                lines = [line for line in lines if line.strip() or line == '\n']

                if not lines:
                    return b'\n'

                # Return first line, buffer the rest
                first_line = lines[0]
                if len(lines) > 1:
                    self._line_buffer.extend(lines[1:])

                # Add newline if not present
                if not first_line.endswith('\n'):
                    first_line += '\n'

                self._last_response = first_line.encode('utf-8')
                print(f"[SocketConnection] readline() returning: {self._last_response.strip()}")
                return self._last_response
            else:
                # Handle bytes responses
                self._last_response = response if isinstance(response, bytes) else response.encode('utf-8')
                return self._last_response

        except Empty:
            # Timeout - return last response or default
            if self._last_response is not None:
                print(f"[SocketConnection] Timeout, returning last response: {self._last_response}")
                return self._last_response
            else:
                print("[SocketConnection] Timeout, returning default 'ok\\n'")
                return b"ok\n"

    @property
    def is_open(self):
        return self._is_open

    def _send_message(self, event, data):
        try:
            current_app.socketio.emit('fabricator_command', {
                'event': event,
                'data': data,
                'fabricator_id': self._fabricator_id
            })
            print(f"Sent {event} via SocketIO for printer {self._fabricator_id}")
        except Exception as e:
            print(f"Failed to send message via SocketIO: {e}")

class EmuListPortInfo(ListPortInfo):
    def __init__(self, device, description=None, hwid=None):
        super().__init__(device)
        self._device = device
        self._description = description
        self._hwid = hwid
        try:
            if hwid and "PID=" in hwid:
                self.vid = int(hwid.split("PID=")[1].split(":")[0], 16)
                self.pid = int(hwid.split(":")[2].split(" ")[0], 16)
            else:
                self.vid = None
                self.pid = None
        except (IndexError, ValueError):
            self.vid = None
            self.pid = None

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
