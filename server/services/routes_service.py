import os
from flask import request, Response, send_from_directory
from routes import defineRoutes

class RoutesService:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup all application routes."""
        # Register API routes
        defineRoutes(self.app)
        
        # Setup static routes
        self.setup_static_routes()
        
        # Setup CORS
        self.setup_cors()
    
    def setup_static_routes(self):
        """Setup static file serving routes."""
        @self.app.route('/')
        def serve_static(path='index.html'):
            return send_from_directory(self.app.static_folder, path)

        @self.app.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(self.app.static_folder, 'assets'), filename)
    
    def setup_cors(self):
        """Setup CORS handling."""
        @self.app.before_request
        def handle_preflight():
            if request.method == "OPTIONS":
                res = Response()
                res.headers['X-Content-Type-Options'] = '*'
                res.headers['Access-Control-Allow-Origin'] = '*'
                res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return res