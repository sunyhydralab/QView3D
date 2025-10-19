import os
from flask import Flask
from dotenv import load_dotenv
from config.paths import root_path
from services.websocket_service import emulator_connections, event_emitter
from config.config import Config
from Classes.FabricatorList import FabricatorList
from services.database_service import DatabaseService
from services.logging_service import LoggingService
from services.socketio_service import SocketIOService
from services.routes_service import RoutesService
from services.cli_service import CLIService
from services.utilities_service import UtilitiesService

class QViewApp(Flask):

    """
    Represents the custom Flask application for QView3D server.
    
    Inherits from Flask and initializes various services and configurations.
    
    Attributes:
        logging_service (LoggingService): Custom logging service for the application.
        database_service (DatabaseService): Database connection and migration management.
        socketio_service (SocketIOService): SocketIO service for real-time communication.
        routes_service (RoutesService): Route definitions and handling.
        cli_service (CLIService): Command-line interface service for the application.
        utilities_service (UtilitiesService): Utility functions for the application.
        fabricator_list (FabricatorList): List of fabricators managed by the application.   
    
    """
    def __init__(self):
        super().__init__(__name__, static_folder=os.path.abspath(os.path.join(root_path, "client", "dist")))

        # Load configuration
        load_dotenv()
        self.config.from_object(__name__)
        self.setup_config()

        # Initialize services
        self.logging_service = LoggingService(self)
        self._logger = self.logging_service.get_logger()
        self.database_service = DatabaseService(self)
        self.socketio_service = SocketIOService(self)
        self.socketio = self.socketio_service.get_socketio()

        # Setup custom variables
        self._fabricator_list = None
        self.emulator_connections = emulator_connections
        self.event_emitter = event_emitter

        # Initialize routes and utilities
        self.routes_service = RoutesService(self)
        self.cli_service = CLIService(self)
        self.utilities_service = UtilitiesService(self)
        self.fabricator_list = FabricatorList(self)

    def setup_config(self):
        """Setup Flask configuration from Config file."""
        self.config["environment"] = Config.get('environment')
        self.config["ip"] = Config.get('ip')
        self.config["port"] = Config.get('port')
        self.config["base_url"] = Config.get('base_url')

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

    # Delegate to services
    def handle_errors_and_logging(self, e, logger=None, level=None):
        """Handle errors and logging by delegating to ErrorService."""
        from services.error_service import ErrorService
        return ErrorService.handle_errors_and_logging(e, logger or self.logger, level)
    
    def get_emu_ports(self):
        """Get emulator ports by delegating to UtilitiesService."""
        return self.utilities_service.get_emu_ports()
    
    def run_go_command(self, command):
        """Run Go command by delegating to UtilitiesService."""
        return self.utilities_service.run_go_command(command)