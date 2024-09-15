from flask import Flask
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.errors import ExceptionMiddleware
from socketio import ASGIApp, SocketIO

# Create a simple Flask app
flask_app = Flask(__name__)

# Initialize SocketIO with Flask
socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode="asgi")

# Create the ASGI app
asgi_app = ASGIApp(socketio, flask_app)

# Wrap ASGI app with CORSMiddleware
asgi_app = CORSMiddleware(
    asgi_app,
    allow_origins=["http://localhost:5173"],  # Adjust this to your front-end URL
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handling middleware
asgi_app = ExceptionMiddleware(
    asgi_app,
    handlers={},
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host="0.0.0.0", port=8000, log_level="debug")
