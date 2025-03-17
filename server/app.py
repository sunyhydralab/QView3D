import os
import shutil
from MyFlaskApp import MyFlaskApp
from globals import tabs
from USB_Detection import setup_monitoring
from models.config import Config

# moved this up here so we can pass the app to the PrinterStatusService
# Basic app setup
print(f"{tabs()}Starting USB detection...")
setup_monitoring()
print(f"{tabs()}USB detection started")
print(f"{tabs()}Starting Flask application...")
app = MyFlaskApp()
print(f"{tabs(tab_change=-1)}Flask application started")

if Config['discord_enabled']:
    print("Starting Discord bot...")
    from Discord_bot import start_discord_bot
    start_discord_bot()
    print("Discord bot started")
else:
    print("Discord bot is disabled")

# own thread
with app.app_context():
    try:
        # Define directory paths for uploads and tempcsv
        uploads_folder = os.path.abspath('../uploads')
        tempcsv = os.path.abspath('../tempcsv')
        # Check if directories exist and handle them accordingly
        for folder in [uploads_folder, tempcsv]:
            if os.path.exists(folder):
                # Remove the folder and all its contents
                shutil.rmtree(folder)
                app.logger.info(f"{folder} removed and will be recreated.")
            # Recreate the folder
            os.makedirs(folder)
            app.logger.info(f"{folder} recreated as an empty directory.")

    except Exception as e:
        # Log any exceptions for troubleshooting
        app.handle_errors_and_logging(e)

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    # since we are using socketio, we need to use socketio.run instead of app.run
    # which passes the app anyways
    run_socketio(app)  # Replace app.run with socketio.run
