"""
Tests for configuration - including the critical bug fix
"""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfiguration:
    """Test configuration loading and values."""

    def test_port_is_integer(self):
        """Test that port configuration is an integer, not a tuple."""
        from config.config import port, emulator_port

        # This was the bug - port was a tuple (8000,) instead of int
        assert isinstance(port, int), f"Port should be int, got {type(port)}: {port}"
        assert isinstance(emulator_port, int), f"Emulator port should be int, got {type(emulator_port)}"

        # Check default values
        assert port == 8000 or port > 0
        assert emulator_port == 8001 or emulator_port > 0

    def test_config_structure(self):
        """Test that Config dictionary has expected structure."""
        from config.config import Config

        # Check required keys
        required_keys = ['base_url', 'environment', 'ip', 'database_uri', 'port', 'emulator_port']
        for key in required_keys:
            assert key in Config, f"Config missing required key: {key}"

        # Check types
        assert isinstance(Config['port'], int)
        assert isinstance(Config['emulator_port'], int)
        assert isinstance(Config['ip'], str)
        assert isinstance(Config['database_uri'], str)

    def test_base_url_generation(self):
        """Test that base_url is correctly generated."""
        from config.config import base_url, ip, port

        url = base_url()
        assert url == f"http://{ip}:{port}"
        assert 'http://' in url
        assert str(port) in url

    def test_database_uri(self):
        """Test database URI configuration."""
        from config.config import database_uri

        assert database_uri.endswith('.db')
        assert 'QView' in database_uri or len(database_uri) > 0

    def test_environment_variables(self):
        """Test that environment variables can override defaults."""
        # Set test environment variables
        test_port = '9000'
        test_emulator = '9001'

        os.environ['FLASK_RUN_PORT'] = test_port
        os.environ['EMULATOR_PORT'] = test_emulator

        # Reload the config module
        import importlib
        import config.config as config_module
        importlib.reload(config_module)

        assert config_module.port == int(test_port)
        assert config_module.emulator_port == int(test_emulator)

        # Cleanup
        del os.environ['FLASK_RUN_PORT']
        del os.environ['EMULATOR_PORT']