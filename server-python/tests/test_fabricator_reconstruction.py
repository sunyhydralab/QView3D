"""
Test fabricator reconstruction from database.
Verifies that @reconstructor properly initializes runtime attributes.
"""
import pytest
from Classes.Fabricators.Fabricator import Fabricator
from config.db import db


def test_fabricator_reconstructor(app):
    """
    Test that fabricator runtime attributes are initialized when loading from database.
    This verifies that the @reconstructor decorator properly initializes attributes
    that SQLAlchemy doesn't persist (queue, status, device, error).
    """
    with app.app_context():
        # Create a test fabricator record directly in the database
        # (bypassing __init__ to simulate a database record)
        from datetime import datetime, timezone

        # Clear any existing test fabricators
        Fabricator.query.filter_by(hwid='TEST_HWID_123').delete()
        db.session.commit()

        # Create a new fabricator using SQL directly to bypass __init__
        test_fab = Fabricator.__new__(Fabricator)
        test_fab.hwid = 'TEST_HWID_123'
        test_fab.name = 'Test Fabricator'
        test_fab.description = 'Test Description'
        test_fab.devicePort = 'ttyUSB0'
        test_fab.date = datetime.now(timezone.utc).astimezone()
        test_fab.model = 'Test Model'

        db.session.add(test_fab)
        db.session.commit()

        test_fab_id = test_fab.dbID

        # Clear the session to force a fresh load from database
        db.session.expunge_all()

        # Load the fabricator from database - this should trigger @reconstructor
        loaded_fab = Fabricator.query.filter_by(dbID=test_fab_id).first()

        # Verify that runtime attributes were initialized by @reconstructor
        assert loaded_fab is not None, "Fabricator should be loaded from database"
        assert hasattr(loaded_fab, 'queue'), "queue attribute should exist"
        assert loaded_fab.queue is not None, "queue should be initialized"
        assert hasattr(loaded_fab, 'status'), "status attribute should exist"
        assert loaded_fab.status == 'offline', "status should default to 'offline'"
        assert hasattr(loaded_fab, 'device'), "device attribute should exist"
        assert loaded_fab.device is None, "device should be None (no active connection)"
        assert hasattr(loaded_fab, 'error'), "error attribute should exist"
        assert loaded_fab.error is None, "error should be None initially"

        # Verify database attributes are preserved
        assert loaded_fab.hwid == 'TEST_HWID_123'
        assert loaded_fab.name == 'Test Fabricator'
        assert loaded_fab.description == 'Test Description'
        assert loaded_fab.devicePort == 'ttyUSB0'

        # Clean up
        Fabricator.query.filter_by(dbID=test_fab_id).delete()
        db.session.commit()


def test_fabricator_queryAll(app):
    """
    Test that queryAll() returns fabricators with initialized runtime attributes.
    """
    with app.app_context():
        from datetime import datetime, timezone

        # Create test fabricators
        Fabricator.query.filter_by(hwid='TEST_HWID_QUERY_1').delete()
        Fabricator.query.filter_by(hwid='TEST_HWID_QUERY_2').delete()
        db.session.commit()

        test_fab1 = Fabricator.__new__(Fabricator)
        test_fab1.hwid = 'TEST_HWID_QUERY_1'
        test_fab1.name = 'Query Test 1'
        test_fab1.description = 'Test'
        test_fab1.devicePort = 'ttyUSB1'
        test_fab1.date = datetime.now(timezone.utc).astimezone()
        test_fab1.model = 'Model 1'

        test_fab2 = Fabricator.__new__(Fabricator)
        test_fab2.hwid = 'TEST_HWID_QUERY_2'
        test_fab2.name = 'Query Test 2'
        test_fab2.description = 'Test'
        test_fab2.devicePort = 'ttyUSB2'
        test_fab2.date = datetime.now(timezone.utc).astimezone()
        test_fab2.model = 'Model 2'

        db.session.add(test_fab1)
        db.session.add(test_fab2)
        db.session.commit()

        # Clear session
        db.session.expunge_all()

        # Use queryAll() to load all fabricators
        all_fabs = Fabricator.queryAll()

        # Find our test fabricators
        test_fabs = [f for f in all_fabs if f.hwid.startswith('TEST_HWID_QUERY')]

        assert len(test_fabs) >= 2, "Should have at least 2 test fabricators"

        # Verify all have initialized runtime attributes
        for fab in test_fabs:
            assert hasattr(fab, 'queue') and fab.queue is not None
            assert hasattr(fab, 'status') and fab.status is not None
            assert hasattr(fab, 'device')
            assert hasattr(fab, 'error')

        # Clean up
        Fabricator.query.filter_by(hwid='TEST_HWID_QUERY_1').delete()
        Fabricator.query.filter_by(hwid='TEST_HWID_QUERY_2').delete()
        db.session.commit()


def test_fabricator_filter_by_query(app):
    """
    Test that filter_by() queries properly initialize runtime attributes.
    """
    with app.app_context():
        from datetime import datetime, timezone

        # Create test fabricator
        Fabricator.query.filter_by(hwid='TEST_HWID_FILTER').delete()
        db.session.commit()

        test_fab = Fabricator.__new__(Fabricator)
        test_fab.hwid = 'TEST_HWID_FILTER'
        test_fab.name = 'Filter Test'
        test_fab.description = 'Test'
        test_fab.devicePort = 'ttyUSB99'
        test_fab.date = datetime.now(timezone.utc).astimezone()
        test_fab.model = 'Filter Model'

        db.session.add(test_fab)
        db.session.commit()

        test_id = test_fab.dbID

        # Clear session
        db.session.expunge_all()

        # Load using filter_by (commonly used in controllers)
        loaded_fab = Fabricator.query.filter_by(dbID=test_id).first()

        # Verify runtime attributes
        assert loaded_fab is not None
        assert hasattr(loaded_fab, 'queue') and loaded_fab.queue is not None
        assert hasattr(loaded_fab, 'status') and loaded_fab.status == 'offline'
        assert hasattr(loaded_fab, 'device') and loaded_fab.device is None
        assert hasattr(loaded_fab, 'error') and loaded_fab.error is None

        # Clean up
        Fabricator.query.filter_by(dbID=test_id).delete()
        db.session.commit()
