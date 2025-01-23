from flask import Flask
from globals import tabs
def defineRoutes(app: Flask):
    # IMPORTING BLUEPRINTS
    print(f"{tabs(tab_change=1)}importing blueprints...", end="")
    from controllers.ports import ports_bp
    from controllers.jobs import jobs_bp
    from controllers.statusService import status_bp
    from controllers.issues import issue_bp
    from controllers.emulator import emulator_bp
    from flask_cors import CORS
    print(" Done")

    print(f"{tabs()}registering CORS...", end="")
    CORS(app)
    print(" Done")
    print(f"{tabs()}registering blueprints...", end="")

    # # Register the display_bp Blueprint
    app.register_blueprint(ports_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(status_bp)
    app.register_blueprint(issue_bp)
    app.register_blueprint(emulator_bp)
    print(" Done")