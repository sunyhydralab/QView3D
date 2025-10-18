import os
import shutil
import threading
import certifi
from QViewApp import QViewApp
from utils.formatting import tabs
from config.config import Config
from services.websocket_service import start_websocket
from services.discord_service import start_discord_bot
from services.logging_service import cleanup_directories

# SSL setup
os.environ["SSL_CERT_FILE"] = certifi.where()

# Start WebSocket server
websocket_thread = threading.Thread(target=start_websocket, daemon=True)
websocket_thread.start()

# Start Flask app
print(f"{tabs()}Starting Flask application...")
app = QViewApp()
print(f"{tabs(tab_change=-1)}Flask application started")

# Start Discord bot
print("Discord bot configuration loaded")
if Config['discord_enabled']:
    print("Starting Discord bot...")
    start_discord_bot()
    print("Discord bot started")
else:
    print("Discord bot is disabled")

# Directory cleanup 
with app.app_context():
    cleanup_directories()

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    run_socketio(app)