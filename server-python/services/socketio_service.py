from flask_socketio import SocketIO

class SocketIOService:
    def __init__(self, app):
        self.app = app
        self.socketio = self.setup_socketio()
        self.setup_events()
    
    def setup_socketio(self):
        """Initialize SocketIO with the Flask app."""
        return SocketIO(self.app, 
                       cors_allowed_origins="*", 
                       engineio_logger=False, 
                       socketio_logger=False,
                       async_mode='eventlet' if self.app.config["environment"] == 'production' else 'threading',
                       transport=['websocket', 'polling'])
    
    def setup_events(self):
        """Setup SocketIO event handlers."""
        @self.socketio.on('ping')
        def handle_ping():
            self.socketio.emit('pong')

        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")
    
    def get_socketio(self):
        return self.socketio