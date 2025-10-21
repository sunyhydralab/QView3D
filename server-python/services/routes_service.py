import os
from flask import request, Response, send_from_directory
from flask_cors import CORS
# Removed tabs import - no longer needed

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
        """Define and register all Flask blueprints."""
        # Import blueprints
        from controllers.ports import ports_bp
        from controllers.jobs import jobs_bp
        from controllers.statusService import status_bp
        from controllers.issues import issue_bp
        from controllers.emulator import emulator_bp

        # Setup CORS
        CORS(self.app)
        
        # Register blueprints
        self.app.register_blueprint(ports_bp)
        self.app.register_blueprint(jobs_bp)
        self.app.register_blueprint(status_bp)
        self.app.register_blueprint(issue_bp)
        self.app.register_blueprint(emulator_bp)
    
    def setup_static_routes(self):
        """Setup static file serving routes."""
        @self.app.route('/')
        def serve_index():
            return send_from_directory(self.app.static_folder, 'index.html')

        @self.app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(self.app.static_folder, 'assets'), filename)

        # Catch-all route for SPA routing - must be last
        @self.app.route('/<path:path>')
        def serve_spa(path):
            """Serve index.html for all non-API routes to support Vue Router."""
            # If it's an API route, let Flask return 404
            if path.startswith('api/') or path.startswith('socket.io/'):
                return {'error': 'Not found'}, 404

            # For all other routes (Vue Router paths), serve index.html
            return send_from_directory(self.app.static_folder, 'index.html')
    
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