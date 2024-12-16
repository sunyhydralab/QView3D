import os
from werkzeug.local import LocalProxy
from Classes.EventEmitter import EventEmitter

# Global variables
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
uploads_folder = os.path.abspath(os.path.join(root_path, 'uploads'))

emulator_connections = {}
event_emitter = EventEmitter()

def _find_custom_app():
    from flask import current_app as flask_current_app
    from MyFlaskApp import MyFlaskApp
    app = flask_current_app._get_current_object()
    return app if isinstance(app, MyFlaskApp) else None

current_app = LocalProxy(_find_custom_app)