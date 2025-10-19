import os
from flask import request, Response, send_from_directory
from flask_cors import CORS
from utils.formatting import tabs

class RoutesService:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all application routes."""
        # Register API blueprints (moved from routes.py)
        self.define_routes()
        
        # Setup static routes
        self.setup_static_routes()
        
        # Setup CORS preflight handling
        self.setup_cors()
    
    def define_routes(self):
        """Define and register all Flask blueprints (moved from routes.py)."""
        # IMPORTING BLUEPRINTS
        print(f"{tabs(tab_change=1)}importing blueprints...", end="")
        from controllers.ports import ports_bp
        from controllers.jobs import jobs_bp
        from controllers.statusService import status_bp
        from controllers.issues import issue_bp
        from controllers.emulator import emulator_bp
        print(" Done")

        print(f"{tabs()}registering CORS...", end="")
        CORS(self.app)
        print(" Done")
        
        print(f"{tabs()}registering blueprints...", end="")
        # Register the blueprints
        self.app.register_blueprint(ports_bp)
        self.app.register_blueprint(jobs_bp)
        self.app.register_blueprint(status_bp)
        self.app.register_blueprint(issue_bp)
        self.app.register_blueprint(emulator_bp)
        print(" Done")
    
    def setup_static_routes(self):
        """Setup static file serving routes."""
        @self.app.route('/')
        def serve_static(path='index.html'):
            return send_from_directory(self.app.static_folder, path)

        @self.app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(self.app.static_folder, 'assets'), filename)
    
    def setup_cors(self):
        """Setup CORS handling for preflight requests."""
        @self.app.before_request
        def handle_preflight():
            if request.method == "OPTIONS":
                res = Response()
                res.headers['X-Content-Type-Options'] = '*'
                res.headers['Access-Control-Allow-Origin'] = '*'
                res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return res