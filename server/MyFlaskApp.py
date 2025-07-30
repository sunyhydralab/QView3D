import logging
import os
import subprocess
from flask import Flask
from dotenv import load_dotenv
from globals import root_path, emulator_connections, event_emitter, tabs
from config.config import Config
from Classes.FabricatorList import FabricatorList
from Classes.Loggers.ABCLogger import ABCLogger
from services.database_service import DatabaseService
from services.logging_service import LoggingService
from services.socketio_service import SocketIOService
from services.routes_service import RoutesService

class MyFlaskApp(Flask):
    def __init__(self):
        print(f"{tabs(tab_change=1)}call to super...", end="")
        super().__init__(__name__, static_folder=os.path.abspath(os.path.join(root_path, "client", "dist")))
        print(" Done")
        
        print(f"{tabs()}loading config...")
        print(f"{tabs(tab_change=1)}loading dotenv...", end="")
        load_dotenv()
        print(" Done")
        
        print(f"{tabs()}loading config from file...", end="")
        self.config.from_object(__name__)
        self.setup_config()
        print(" Done")
        
        # Initialize services
        print(f"{tabs()}setting up logging service...", end=" ")
        self.logging_service = LoggingService(self)
        self._logger = self.logging_service.get_logger()
        print("Done")
        
        print(f"{tabs(tab_change=-1)}initializing db...", end="")
        self.database_service = DatabaseService(self)
        print(" Done")
        
        print(f"{tabs()}setting up SocketIO...", end="")
        self.socketio_service = SocketIOService(self)
        self.socketio = self.socketio_service.get_socketio()
        print(" Done")
        
        print(f"{tabs()}setting up custom variables...", end="")
        self._fabricator_list = None
        self.emulator_connections = emulator_connections
        self.event_emitter = event_emitter
        print(" Done")
        
        print(f"{tabs()}defining routes...")
        self.routes_service = RoutesService(self)
        print(f"{tabs(tab_change=-1)}routes defined")
        
        print(f"{tabs()}initializing fabricator list...")
        self.fabricator_list = FabricatorList(self)
        print(f"{tabs(tab_change=-1)}fabricator list initialized")
        
        # Setup CLI commands
        self.setup_cli_commands()
        
        print(f"{tabs()}Flask app setup complete")

    def setup_config(self):
        """Setup Flask configuration from Config file."""
        self.config["environment"] = Config.get('environment')
        self.config["ip"] = Config.get('ip')
        self.config["port"] = Config.get('port')
        self.config["base_url"] = Config.get('base_url')
    
    def setup_cli_commands(self):
        """Setup Flask CLI commands."""
        @self.cli.command("test")
        def run_tests():
            """Run all tests."""
            import subprocess
            subprocess.run(["python", "../Tests/parallel_test_runner.py"])

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