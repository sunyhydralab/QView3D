import os
import threading
import certifi
from QViewApp import QViewApp
from services.websocket_service import start_websocket

# SSL setup
os.environ["SSL_CERT_FILE"] = certifi.where()

# Start WebSocket server
websocket_thread = threading.Thread(target=start_websocket, daemon=True)
websocket_thread.start()

# Start Flask app
app = QViewApp()

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    run_socketio(app)