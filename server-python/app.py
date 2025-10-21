import os
import certifi
from QViewApp import QViewApp

# SSL setup
os.environ["SSL_CERT_FILE"] = certifi.where()

# Start Flask app (WebSocket now integrated into SocketIO service)
app = QViewApp()

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    run_socketio(app)