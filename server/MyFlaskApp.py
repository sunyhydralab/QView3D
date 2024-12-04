import logging
import os
import sys

from flask import request, Response, send_from_directory, Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_socketio import SocketIO
from globals import root_path, emulator_connections, event_emitter
from routes import defineRoutes
from models.config import Config
from Classes.FabricatorList import FabricatorList
from models.db import db

class MyFlaskApp(Flask):
    def __init__(self):
        super().__init__(__name__, static_folder=os.path.abspath(os.path.join(root_path, "client", "dist")))
        load_dotenv()
        basedir = os.path.abspath(os.path.join(root_path, "server"))
        database_file = os.path.abspath(os.path.join(basedir, Config.get('database_uri')))
        if isinstance(database_file, bytes):
            database_file = database_file.decode('utf-8')
        databaseuri = 'sqlite:///' + database_file
        self.config['SQLALCHEMY_DATABASE_URI'] = databaseuri
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self)
        Migrate(self, db)
        self._fabricator_list = None
        self._logger = None
        from Classes.Logger import Logger
        logs = os.path.join(root_path, "server", "logs")
        os.makedirs(logs, exist_ok=True)
        self.logger = Logger("App", consoleLogger=sys.stdout, fileLogger=os.path.abspath(os.path.join(logs, f"{__name__}.log")),
                            consoleLevel=logging.ERROR)
        self.config.from_object(__name__) # update application instantly
        # start database connection
        self.config["environment"] = Config.get('environment')
        self.config["ip"] = Config.get('ip')
        self.config["port"] = Config.get('port')
        self.config["base_url"] = Config.get('base_url')

        self.socketio = SocketIO(self, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False,
                            async_mode='eventlet' if self.config["environment"] == 'production' else 'threading',
                            transport=['websocket', 'polling'])  # make it eventlet on production!

        self.emulator_connections = emulator_connections
        self.event_emitter = event_emitter

        CORS(self)

        # Register all routes
        defineRoutes(self)

        self.fabricator_list = FabricatorList(self)

        @self.cli.command("test")
        def run_tests():
            """Run all tests."""
            import subprocess
            subprocess.run(["python", "../Tests/parallel_test_runner.py"])

        @self.before_request
        def handle_preflight():
            if request.method == "OPTIONS":
                res = Response()
                res.headers['X-Content-Type-Options'] = '*'
                res.headers['Access-Control-Allow-Origin'] = '*'
                res.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return res

        # Serve static files
        @self.route('/')
        def serve_static(path='index.html'):
            return send_from_directory(self.static_folder, path)

        @self.route('/assets/<path:filename>')
        def serve_assets(filename):
            return send_from_directory(os.path.join(self.static_folder, 'assets'), filename)

        @self.socketio.on('ping')
        def handle_ping():
            self.socketio.emit('pong')

        @self.socketio.on('connect')
        def handle_connect():
            print("Client connected")


    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @logger.getter
    def logger(self):
        return self._logger

    @property
    def fabricator_list(self):
        return self._fabricator_list

    @fabricator_list.setter
    def fabricator_list(self, fabricator_list):
        self._fabricator_list = fabricator_list

    @fabricator_list.getter
    def fabricator_list(self):
        return self._fabricator_list

    def handle_errors_and_logging(self, e: Exception | str, fabricator=None):
        from Classes.Fabricators.Fabricator import Fabricator
        device = fabricator
        if isinstance(fabricator, Fabricator):
            device = fabricator.device
        if device is not None and hasattr(device, "logger") and device.logger is not None:
            device.logger.error(e, stacklevel=3)
        elif self.logger is None:
            if isinstance(e, str):
                print(e.strip())
            else:
                import traceback
                print(traceback.format_exception(None, e, e.__traceback__))
        else:
            self.logger.error(e, stacklevel=3)
        return False

    def get_emu_ports(self):
        fake_device = next(iter(self.emulator_connections.values()), None)
        if fake_device:
            return [fake_device.fake_port, fake_device.fake_name, fake_device.fake_hwid]
        return [None, None, None]