import asyncio
import re
import threading
import uuid
import serial
import json
from queue import Queue, Empty
from abc import ABC
from serial.tools.list_ports import grep
from serial.tools.list_ports_common import ListPortInfo
from globals import current_app as app
from pyvisa.resources.resource import Resource
from pyvisa.resources import SerialInstrument
from pyvisa import ResourceManager, constants


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
        :rtype: Resource | SocketConnection
        """
        if websocket_connections is not None and fabricator_id is not None:
            return SocketConnection(port, baudrate, websocket_connections, fabricator_id, timeout=timeout)
        elif port is not None and baudrate is not None:
            if re.match(r"COM\d+", port):
                port = f"ASRL{re.sub(r"COM", "", port)}::INSTR"
            elif not re.match(r"ASRL\d+::INSTR", port):
                raise ValueError(f"Invalid serial port format: {port}")
            if app.resource_manager.list_opened_resources():
                for resource in app.resource_manager.list_opened_resources():
                    if port == resource.resource_name:
                        return resource
            return app.resource_manager.open_resource(port, baud_rate=baudrate, timeout=timeout)
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

class CustomResourceManager(ResourceManager):
    def __init__(self):
        super().__init__()

    def open_resource(self, resource_name, **kwargs):
        """Ensure serial instruments are instantiated using CustomSerialInstrument."""
        if resource_name and re.match(r"COM\d+", resource_name):
            resource_name = f"{re.sub(r'COM', 'ASRL', resource_name)}::INSTR"
        open_resources = self.list_opened_resources()
        if open_resources and any(resource.resource_name == resource_name for resource in open_resources):
            return next((res for res in self.list_opened_resources() if res.resource_name == resource_name), None)
        if re.match(r"ASRL\d+::INSTR", resource_name):
            printer = CustomSerialInstrument(self, resource_name, **kwargs)
            self._created_resources.add(printer)
            return printer

        return super().open_resource(resource_name, **kwargs)

    def list_resources(self, query=""):
        return super().list_resources(query)

    def list_opened_resources(self):
        return super().list_opened_resources()

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

