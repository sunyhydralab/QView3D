from Classes.EventEmitter import EventEmitter

emulator_connections = {}
event_emitter = EventEmitter()

def get_emulator_connections():
    from services.app_service import current_app
    if hasattr(current_app, 'socketio_service'):
        return current_app.socketio_service.get_emulator_connections()
    return {}
