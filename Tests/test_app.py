import os
import re
import pytest
from Classes.Logger import Logger
from parallel_test_runner import testLevel
from app import app
def __desc__(): return "App Tests"
with app.app_context():
    @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
    def test_db():
        db_file_no_path = app.config["SQLALCHEMY_DATABASE_URI"].split("/")[-1].split("\\")[-1]
        assert db_file_no_path, "database_uri doesn't exist?"
        assert db_file_no_path == "hvamc.db", f"database_uri is {db_file_no_path}"
        assert os.path.exists(app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[-1]), f"Database file {app.config["SQLALCHEMY_DATABASE_URI"].split("sqlite:///")[-1]} does not exist"

    @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
    def test_base_url():
        assert app.config["base_url"], "base_url doesnt exist?"
        assert re.match(r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}$", app.config["base_url"]) or re.match(r"http://localhost:\d{1,5}$", app.config["base_url"]), f"base_url is {app.config['base_url']}"

    @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
    def test_environment():
        assert app.config["environment"], "environment doesnt exist?"
        assert app.config["environment"] == "development", f"environment is {app.config['environment']}"

    @pytest.mark.skipif(condition=testLevel < 1, reason="Not doing lvl 1 tests")
    def test_logger():
        assert app.logger, "myLogger doesnt exist?"
        assert app.logger.name, "name doesnt exist?"
        assert str(app.logger.name) == "Logger_App", f"myLogger is {str(app.logger.name)}"
        assert isinstance(app.logger, Logger), "myLogger is not an instance of Logger?"
        assert app.logger.fileLogger, "fileLogger doesnt exist?"
        assert app.logger.consoleLogger, "consoleLogger doesn't exists?"
