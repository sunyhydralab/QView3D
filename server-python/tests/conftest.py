"""
Pytest configuration and fixtures for QView3D tests
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import your app and database
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.db import db as _db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app()

    # Configure for testing
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key'
    })

    # Create application context
    with app.app_context():
        yield app


@pytest.fixture(scope='session')
def db(app):
    """Create database for testing."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(scope='function')
def session(app, db):
    """Create a clean database session for each test."""
    from sqlalchemy.orm import scoped_session

    connection = db.engine.connect()
    transaction = connection.begin()

    # Create scoped session for proper cleanup
    Session = scoped_session(sessionmaker(bind=connection))

    # Store original session and teardown functions
    original_session = db.session

    # Replace with our test session
    db.session = Session

    yield Session

    # Cleanup
    Session.remove()
    transaction.rollback()
    connection.close()

    # Restore original session
    db.session = original_session


@pytest.fixture(scope='function')
def client(app):
    """Create a test client for the app."""
    return app.test_client()


@pytest.fixture
def sample_job_data():
    """Sample job data for testing."""
    return {
        'name': 'Test Print Job',
        'file_name_original': 'test_model.gcode',
        'printer_id': 1,
        'status': 'pending',
        'favorite': False,
        'td_id': 12345,
        'filament': 'PLA'
    }


@pytest.fixture
def sample_fabricator_data():
    """Sample fabricator data for testing."""
    return {
        'name': 'Test Printer',
        'model': 'Prusa MK4',
        'serial_port': 'COM3',
        'status': 'idle'
    }


@pytest.fixture
def mock_gcode_file():
    """Create a mock G-code file for testing."""
    content = b""";FLAVOR:Marlin
;TIME:3600
;Layer height: 0.2
;LAYER_CHANGE
;Z:0.2
G28 ; Home all axes
M104 S200 ; Set hotend temp
M140 S60 ; Set bed temp
M109 S200 ; Wait for hotend
M190 S60 ; Wait for bed
G1 X10 Y10 Z0.2 F3000
G1 X100 Y10 E10
G1 X100 Y100 E20
M104 S0 ; Cool hotend
M140 S0 ; Cool bed
M84 ; Disable motors
"""

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.gcode', delete=False) as f:
        f.write(content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def auth_headers():
    """Mock authentication headers for protected endpoints."""
    # This would normally include JWT tokens or session cookies
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }