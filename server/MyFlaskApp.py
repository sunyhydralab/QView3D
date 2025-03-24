import logging
import os
import subprocess
import sys

from pyvisa import constants
from flask import request, Response, send_from_directory, Flask
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_socketio import SocketIO

# from Classes.MyPyVISA.CustomResourceManager import CustomResourceManager
from pyvisa import ResourceManager
from Classes.MyPyVISA.CustomSerialInstrument import CustomSerialInstrument
from Classes.MyPyVISA.CustomTCPIPInstrument import CustomTCPIPInstrument
from globals import root_path, emulator_connections, event_emitter, tabs
from routes import defineRoutes
from models.config import Config
from Classes.FabricatorList import FabricatorList
from Classes.Loggers.ABCLogger import ABCLogger
from models.db import db
from werkzeug.serving import WSGIRequestHandler
from My_Signal import setup_signal

class MyFlaskApp(Flask):
    def __init__(self):
        print(f"{tabs(tab_change=1)}call to super...", end=" ")
        super().__init__(__name__, static_folder=os.path.abspath(os.path.join(root_path, "client", "dist")))
        print("Done")
        print(f"{tabs()}setting up werkzeug logging...", end=" ")
        # Get the werkzeug logger
        logger = logging.getLogger('werkzeug')
        # Change the output stream to stdout
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(sys.stdout)
        # Ensure Werkzeug's request handler also logs to stdout
        WSGIRequestHandler.log = lambda self, type, message, *args: print(f"{self.address_string().replace("%", "%%")} - - [{self.log_date_time_string()}] {message % args}", file=sys.stdout)
        print("Done")
        print(f"{tabs()}loading config...")
        print(f"{tabs(tab_change=1)}loading dotenv...", end=" ")
        load_dotenv()
        print("Done")
        print(f"{tabs()}loading config from file...", end=" ")
        self.config.from_object(__name__)  # update application instantly
        # start database connection
        self.config["environment"] = Config.get('environment')
        self.config["ip"] = Config.get('ip')
        self.config["port"] = Config.get('port')
        self.config["base_url"] = Config.get('base_url')
        basedir = os.path.abspath(os.path.join(root_path, "server"))
        database_file = os.path.abspath(os.path.join(basedir, Config.get('database_uri')))
        if isinstance(database_file, bytes):
            database_file = database_file.decode('utf-8')
        database_uri = 'sqlite:///' + database_file
        self.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        self.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        print(f"Done")
        print(f"{tabs(tab_change=-1)}config loaded")
        print(f"{tabs()}initializing db...", end=" ")
        db.init_app(self)
        Migrate(self, db)
        print(f"Done")
        print(f"{tabs()}setting up custom variables...")
        self._resource_manager = ResourceManager("@py")
        self.resource_manager.register_resource_class(constants.InterfaceType.asrl, "INSTR", CustomSerialInstrument)
        self.resource_manager.register_resource_class(constants.InterfaceType.tcpip, "INSTR", CustomTCPIPInstrument)
        self.resource_manager.register_resource_class(constants.InterfaceType.tcpip, "SOCKET", CustomTCPIPInstrument)
        # self._resource_manager = CustomResourceManager()
        print(f"{tabs(tab_change=1)}checking for registered resource classes...")
        print(f"{tabs(tab_change=1)}registered resource classes:")
        tabs(tab_change=1)
        for cls in self.resource_manager._resource_classes:
            print(f"{tabs()}{cls}: {self.resource_manager._resource_classes[cls]}")
        print(f"{tabs(tab_change=-1)}Done")
        self._fabricator_list = None
        self._logger = None
        from Classes.Loggers.Logger import Logger
        logs = os.path.join(root_path, "logs")
        os.makedirs(logs, exist_ok=True)
        self.logger = Logger("App", consoleLogger=sys.stdout, fileLogger=os.path.abspath(os.path.join(logs, f"{__name__}.log")),
                            consoleLevel=logging.ERROR)

        self.socketio = SocketIO(self, cors_allowed_origins="*", engineio_logger=False, socketio_logger=False,
                            async_mode='eventlet' if self.config["environment"] == 'production' else 'threading',
                            transport=['websocket', 'polling'])  # make it eventlet on production!

        self.emulator_connections = emulator_connections
        self.event_emitter = event_emitter
        print(f"{tabs(tab_change=-1)}Done")
        print(f"{tabs(tab_change=-1)}Done")
        print(f"{tabs()}defining routes...")
        # Register all routes
        defineRoutes(self)
        print(f"{tabs(tab_change=-1)}routes defined")
        print(f"{tabs()}initializing fabricator list...")
        self.fabricator_list = FabricatorList(self)
        setup_signal(self.teardown)
        print(f"{tabs(tab_change=-1)}fabricator list initialized")
        # TODO: figure out how to run the emu from here
        # emu_path = os.path.abspath(os.path.join(".", root_path, "printeremu", "cmd", "test_printer.go"))
        # self.run_go_command(f"go run .\\{emu_path} 1 -conn")

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

        print(f"{tabs()}setting up static routes...", end=" ")

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

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Client disconnected")

        print("Done")


    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    @property
    def fabricator_list(self):
        return self._fabricator_list

    @fabricator_list.setter
    def fabricator_list(self, fabricator_list):
        self._fabricator_list = fabricator_list

    @property
    def resource_manager(self):
        return self._resource_manager

    def teardown(self, signum, frame):
        self.fabricator_list.teardown()
        from USB_Detection import monitor
        monitor.stop_monitoring()
        exit(signum if signum else 0)


    def handle_errors_and_logging(self, e: Exception | str, logger=None, level=logging.ERROR):
        """
        Handles errors and logs them
        :param Exception | str e: the exception to handle
        :param ABCLogger | None logger: the logger to use
        :param int level: the logging level
        """
        if logger is not None:
            logger.log(level, e, stacklevel=5)
        elif self.logger is None:
            if isinstance(e, str):
                print(e.strip())
            else:
                import traceback
                print(traceback.format_exception(None, e, e.__traceback__))
        else:
            self.logger.log(level, e, stacklevel=5)
        return False

    def get_emu_ports(self):
        fake_device = next(iter(self.emulator_connections.values()), None)
        if fake_device:
            return [fake_device.fake_port, fake_device.fake_name, fake_device.fake_hwid]
        return [None, None, None]

    def run_go_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return result.stdout.decode('utf-8')
        except subprocess.CalledProcessError as e:
            self.handle_errors_and_logging(e)
            return None