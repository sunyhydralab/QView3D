from flask_socketio import SocketIO
from flask import request
import logging

class SocketIOService:
    def __init__(self, app):
        self.app = app
        self.socketio = self.setup_socketio()
        self.emulator_connections = {}
        self.setup_events()
        self.logger = logging.getLogger("socketio")

    def setup_socketio(self):
        return SocketIO(self.app,
                       cors_allowed_origins="*",
                       engineio_logger=False,
                       socketio_logger=False,
                       async_mode='eventlet' if self.app.config["environment"] == 'production' else 'threading',
                       transport=['websocket', 'polling'])

    def setup_events(self):
        @self.socketio.on('ping')
        def handle_ping():
            self.socketio.emit('pong')

        @self.socketio.on('connect')
        def handle_connect():
            sid = request.sid
            print(f"Client connected: {sid}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            sid = request.sid
            print(f"Client disconnected: {sid}")
            if sid in self.emulator_connections:
                del self.emulator_connections[sid]

        @self.socketio.on('emulator_identify')
        def handle_emulator_identify(data):
            sid = request.sid
            self.logger.debug(f"Emulator identifying: {sid}")

            fake_port = data.get('port')
            fake_name = data.get('Name') or data.get('name')
            fake_hwid = data.get('Hwid') or data.get('hwid')

            if fake_port and fake_name and fake_hwid:
                self.emulator_connections[sid] = {
                    'fake_port': fake_port,
                    'fake_name': fake_name,
                    'fake_hwid': fake_hwid,
                    'sid': sid
                }

                msg = f"Emulator connected: {fake_name} ({fake_hwid}) on port {fake_port}"
                print(msg)
                self.logger.debug(msg)

                self.socketio.emit('emulator_identified', {'success': True}, room=sid)
            else:
                self.logger.error(f"Invalid emulator identification data: {data}")
                self.socketio.emit('emulator_identified', {'success': False, 'error': 'Missing identification data'}, room=sid)

        @self.socketio.on('emulator_message')
        def handle_emulator_message(data):
            sid = request.sid
            self.logger.debug(f"Received message from emulator {sid}: {data}")
            self.socketio.emit('emulator_update', data, broadcast=True)

        @self.socketio.on('fabricator_command')
        def handle_fabricator_command(data):
            """Forward backend commands to emulator"""
            event_type = data.get('event', '')
            event_data = data.get('data', {})
            fabricator_id = data.get('fabricator_id', '')

            self.logger.debug(f"Forwarding fabricator_command: {event_type} for {fabricator_id}")

            # Map backend events to emulator events
            if event_type == 'send_gcode':
                # Forward to emulator with correct format
                self.socketio.emit('send_gcode', {
                    'port': event_data.get('printerid', fabricator_id),
                    'gcode': event_data.get('gcode', '')
                })

        @self.socketio.on('gcode_response')
        def handle_gcode_response(data):
            """Forward emulator gcode responses to event emitter for SocketConnection"""
            sid = request.sid
            self.logger.debug(f"Received gcode_response from {sid}: {data}")
            from services.app_service import current_app
            import json

            # Get the fabricator port/ID from the response
            fabricator_id = data.get('port', '')
            if fabricator_id:
                # Emit to the specific fabricator's listener
                listener_id = f"gcode_response_{fabricator_id}"
                current_app.event_emitter.emit(listener_id, json.dumps(data))

    def get_socketio(self):
        return self.socketio

    def get_emulator_connections(self):
        return self.emulator_connections