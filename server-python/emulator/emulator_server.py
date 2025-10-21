"""
QView3D Python Emulator Server

Runs a SocketIO server on port 8004 that simulates 3D printer behavior.
Connects to the main backend on port 8000 to register emulated printers.
"""

import json
import os
import sys
import time
import requests
from flask import Flask, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading

# Add parent directory to path to import emulator modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emulator.emulated_device import EmulatedDevice
from emulator.gcode_simulator import GCodeSimulator

class EmulatorServer:
    def __init__(self, config_path=None):
        """Initialize the emulator server"""
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'emulator_config.json')

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Server configuration
        self.port = self.config.get('emulator', {}).get('port', 8004)
        self.backend_url = self.config.get('emulator', {}).get('backend_url', 'http://localhost:8000')
        self.auto_register = self.config.get('emulator', {}).get('auto_register', True)

        # Create Flask app
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['SECRET_KEY'] = 'emulator_secret_key'

        # Create SocketIO instance
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading'
        )

        # Emulated devices storage
        self.devices = {}  # {port: EmulatedDevice}

        # Setup event handlers
        self.setup_events()

        print(f"[Emulator] Initialized with backend: {self.backend_url}")

    def setup_events(self):
        """Setup SocketIO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            print(f"[Emulator] Client connected: {request.sid}")
            emit('connected', {'message': 'Connected to emulator server'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"[Emulator] Client disconnected: {request.sid}")

        @self.socketio.on('create_emulator')
        def handle_create_emulator(data):
            """Create a new emulated printer"""
            try:
                name = data.get('name', 'Emulated Printer')
                model = data.get('model', 'Prusa MK4')

                # Create emulated device
                device = EmulatedDevice(self.config, name=name, model=model)
                device.connect()

                # Store device
                self.devices[device.port] = device

                print(f"[Emulator] Created device: {device.name} ({device.port})")

                # Register with backend if auto_register is enabled
                if self.auto_register:
                    self.register_with_backend(device)

                emit('emulator_created', {
                    'success': True,
                    'device': device.to_dict()
                })

            except Exception as e:
                print(f"[Emulator] Error creating device: {e}")
                emit('emulator_created', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('send_gcode')
        def handle_send_gcode(data):
            """Send G-code command to emulated device"""
            try:
                port = data.get('port')
                gcode = data.get('gcode', '')

                if port not in self.devices:
                    emit('gcode_response', {
                        'success': False,
                        'error': 'Device not found'
                    })
                    return

                device = self.devices[port]
                response, delay = device.send_command(gcode)

                # Simulate delay if realistic delays are enabled
                if self.config.get('simulation', {}).get('realistic_delays', True) and delay > 0:
                    time.sleep(min(delay, 5.0))  # Cap at 5 seconds

                emit('gcode_response', {
                    'success': True,
                    'port': port,
                    'command': gcode,
                    'response': response,
                    'state': device.get_state()
                })

            except Exception as e:
                print(f"[Emulator] Error processing G-code: {e}")
                emit('gcode_response', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('get_state')
        def handle_get_state(data):
            """Get current state of emulated device"""
            try:
                port = data.get('port')

                if port not in self.devices:
                    emit('device_state', {
                        'success': False,
                        'error': 'Device not found'
                    })
                    return

                device = self.devices[port]
                emit('device_state', {
                    'success': True,
                    'port': port,
                    'state': device.get_state()
                })

            except Exception as e:
                print(f"[Emulator] Error getting state: {e}")
                emit('device_state', {
                    'success': False,
                    'error': str(e)
                })

        @self.socketio.on('list_devices')
        def handle_list_devices():
            """List all emulated devices"""
            devices_list = [device.to_dict() for device in self.devices.values()]
            emit('devices_list', {
                'success': True,
                'devices': devices_list
            })

    def register_with_backend(self, device: EmulatedDevice):
        """Register emulated device with the main backend"""
        try:
            # Send registration request to backend
            response = requests.post(
                f"{self.backend_url}/api/emulator/create",
                json={
                    'name': device.name,
                    'model': device.model,
                    'port': device.port
                },
                timeout=5
            )

            if response.status_code == 200:
                print(f"[Emulator] Successfully registered {device.name} with backend")

                # Emit identification event via SocketIO
                backend_socket_url = self.backend_url.replace('http://', 'ws://')
                # Note: For full SocketIO integration, we'd connect as a client here
                # For now, the HTTP API registration is sufficient

                return True
            else:
                print(f"[Emulator] Failed to register with backend: {response.status_code}")
                return False

        except Exception as e:
            print(f"[Emulator] Error registering with backend: {e}")
            return False

    def create_default_printers(self):
        """Create default printers from config"""
        default_printers = self.config.get('emulator', {}).get('default_printers', [])

        for printer_config in default_printers:
            try:
                name = printer_config.get('name', 'Emulated Printer')
                model = printer_config.get('model', 'Generic 3D Printer')

                device = EmulatedDevice(self.config, name=name, model=model)
                device.connect()
                self.devices[device.port] = device

                print(f"[Emulator] Created default device: {device.name} ({device.port})")

                if self.auto_register:
                    self.register_with_backend(device)

            except Exception as e:
                print(f"[Emulator] Error creating default printer: {e}")

    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the emulator server"""
        if port is None:
            port = self.port

        print('\n' + '='*60)
        print('QView3D Python Emulator Server')
        print('='*60)
        print(f'Emulator:     http://localhost:{port}')
        print(f'Backend:      {self.backend_url}')
        print(f'Auto-register: {self.auto_register}')
        print('='*60 + '\n')

        # Create default printers
        self.create_default_printers()

        # Run SocketIO server
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )


def main():
    """Main entry point for emulator server"""
    emulator = EmulatorServer()
    emulator.run()


if __name__ == '__main__':
    main()
