from werkzeug.local import LocalProxy

def _find_custom_app():
    """Function to find the custom Flask app instance."""
    from flask import current_app as flask_current_app
    from QViewApp import QViewApp
    app = flask_current_app._get_current_object()
    return app if isinstance(app, QViewApp) else None

current_app = LocalProxy(_find_custom_app)