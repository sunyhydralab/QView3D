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

    def get_socketio(self):
        return self.socketio

    def get_emulator_connections(self):
        return self.emulator_connections