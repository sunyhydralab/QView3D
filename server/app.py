import os
import shutil
import threading
import certifi
from QViewApp import QViewApp
from globals import tabs
from config.config import Config
from services.websocket_service import start_websocket
from services.discord_service import start_discord_bot

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
    try:
        uploads_folder = os.path.abspath('../uploads')
        tempcsv = os.path.abspath('../tempcsv')
        for folder in [uploads_folder, tempcsv]:
            if os.path.exists(folder):
                shutil.rmtree(folder)
                app.logger.info(f"{folder} removed and will be recreated.")
            os.makedirs(folder)
            app.logger.info(f"{folder} recreated as an empty directory.")
    except Exception as e:
        app.handle_errors_and_logging(e)

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    run_socketio(app)