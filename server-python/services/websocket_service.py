"""
DEPRECATED: WebSocket Service

This module is no longer used for standalone WebSocket servers.
Emulator WebSocket functionality has been merged into the main SocketIO service.

For emulator connections, use the SocketIO service with these events:
- 'emulator_identify': Sent by emulator to identify itself
- 'emulator_message': General messages from emulator
- 'emulator_update': Broadcast updates about emulator state

Access emulator connections via:
app.socketio_service.get_emulator_connections()
"""

from Classes.EventEmitter import EventEmitter

# Legacy exports for backward compatibility
emulator_connections = {}
event_emitter = EventEmitter()

def get_emulator_connections():
    """
    DEPRECATED: Use app.socketio_service.get_emulator_connections() instead.
    This is kept for backward compatibility only.
    """
    from services.app_service import current_app
    if hasattr(current_app, 'socketio_service'):
        return current_app.socketio_service.get_emulator_connections()
    return {}
