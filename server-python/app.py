import os
import certifi
from QViewApp import QViewApp

# SSL setup
os.environ["SSL_CERT_FILE"] = certifi.where()

def create_app(config_override=None):
    """
    Application factory function that creates and configures a QViewApp instance.

    Args:
        config_override (dict, optional): Dictionary of configuration values to override.

    Returns:
        QViewApp: Configured application instance.
    """
    app = QViewApp()

    # Apply configuration overrides if provided
    if config_override:
        app.config.update(config_override)

    return app

def run_socketio(app):
    try:
        app.socketio.run(app, allow_unsafe_werkzeug=True, port=8000)
    except Exception as e:
        app.handle_errors_and_logging(e)

if __name__ == "__main__":
    app = create_app()
    run_socketio(app)