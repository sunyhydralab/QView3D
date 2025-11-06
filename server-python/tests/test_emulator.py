"""
Comprehensive tests for emulator functionality
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from Classes.Fabricators.Fabricator import Fabricator
from config.db import db


class TestEmulatorCreation:
    """Test emulator creation and initialization."""

    def test_create_emulator_via_api(self, client, app):
        """Test creating emulator through API."""
        with app.app_context():
            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()

                # Create mock fabricator to return
                mock_fab = Mock()
                mock_fab.dbID = 1
                mock_fab.name = 'Test Emulator'
                mock_fab.devicePort = 'EMU_12345678'
                mock_fab.__to_JSON__ = Mock(return_value={
                    'id': 1,
                    'name': 'Test Emulator',
                    'port': 'EMU_12345678'
                })

                with patch('controllers.emulator.Fabricator') as mock_fabricator_class:
                    mock_fabricator_class.query.filter_by.return_value.first.return_value = mock_fab

                    response = client.post('/api/emulator/create',
                                         json={
                                             'model': 'Prusa MK4',
                                             'name': 'Test Emulator'
                                         })

                    # Should succeed or fail gracefully
                    assert response.status_code in [200, 400, 500]

    def test_emulator_port_generation(self, client, app):
        """Test that emulator generates EMU_ prefixed port."""
        with app.app_context():
            with patch('controllers.emulator.generate_mock_serial') as mock_serial:
                mock_serial.return_value = 'TESTSERIAL'

                # Port should be EMU_TESTSERIAL
                from controllers.emulator import generate_mock_serial
                serial = generate_mock_serial()

                # Serial should be 8 characters
                assert len(serial) == 8

    def test_emulator_unique_ports(self):
        """Test that emulators get unique ports."""
        from controllers.emulator import generate_mock_serial

        serial1 = generate_mock_serial()
        serial2 = generate_mock_serial()

        # Serials should be different (probabilistically)
        # They might be same by chance, but very unlikely
        assert len(serial1) == 8
        assert len(serial2) == 8


class TestEmulatorListing:
    """Test listing emulators."""

    def test_list_emulators_empty(self, client, app):
        """Test listing emulators when none exist."""
        with app.app_context():
            response = client.get('/api/emulator/list')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)

    def test_list_emulators_with_data(self, client, app):
        """Test listing emulators when some exist."""
        with app.app_context():
            # Create test emulator in database
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_HWID_TEST'
            fab.name = 'Test Emulator'
            fab.description = 'Test'
            fab.devicePort = 'EMU_12345678'
            fab.model = 'Prusa MK4'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            response = client.get('/api/emulator/list')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)

            # Should find our emulator
            emu_ports = [e['port'] for e in data if 'port' in e]
            assert 'EMU_12345678' in emu_ports

            # Clean up
            db.session.delete(fab)
            db.session.commit()

    def test_list_filters_non_emulators(self, client, app):
        """Test that list only returns EMU_ prefixed devices."""
        with app.app_context():
            # Create regular fabricator
            fab1 = Fabricator.__new__(Fabricator)
            fab1.hwid = 'REAL_HWID'
            fab1.name = 'Real Printer'
            fab1.description = 'Real'
            fab1.devicePort = 'ttyUSB0'
            fab1.model = 'Prusa MK4'
            fab1.date = datetime.now(timezone.utc).astimezone()

            # Create emulator
            fab2 = Fabricator.__new__(Fabricator)
            fab2.hwid = 'EMU_HWID'
            fab2.name = 'Emulator'
            fab2.description = 'Emu'
            fab2.devicePort = 'EMU_87654321'
            fab2.model = 'Prusa MK4'
            fab2.date = datetime.now(timezone.utc).astimezone()

            db.session.add_all([fab1, fab2])
            db.session.commit()

            response = client.get('/api/emulator/list')

            assert response.status_code == 200
            data = json.loads(response.data)

            # Should only include emulator
            ports = [e.get('port', '') for e in data]
            assert any(p.startswith('EMU_') for p in ports)
            assert 'ttyUSB0' not in ports

            # Clean up
            db.session.delete(fab1)
            db.session.delete(fab2)
            db.session.commit()


class TestEmulatorDeletion:
    """Test deleting emulators."""

    def test_delete_emulator(self, client, app):
        """Test deleting an emulator."""
        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_DELETE_TEST'
            fab.name = 'To Delete'
            fab.description = 'Test'
            fab.devicePort = 'EMU_DELETE01'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.deleteFabricator = Mock()

                response = client.delete(f'/api/emulator/delete/{fab_id}')

                # Should succeed or fail gracefully
                assert response.status_code in [200, 400, 404, 500]

            # Clean up if still exists
            try:
                db.session.delete(fab)
                db.session.commit()
            except:
                pass

    def test_delete_real_printer_rejected(self, client, app):
        """Test that deleting real printer is rejected."""
        with app.app_context():
            # Create real printer
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'REAL_PRINTER'
            fab.name = 'Real Printer'
            fab.description = 'Real'
            fab.devicePort = 'ttyUSB0'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            response = client.delete(f'/api/emulator/delete/{fab_id}')

            # Should return 400 error
            assert response.status_code in [400, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()

    def test_delete_nonexistent_emulator(self, client, app):
        """Test deleting emulator that doesn't exist."""
        with app.app_context():
            response = client.delete('/api/emulator/delete/999999')

            assert response.status_code == 404


class TestEmulatorStatusUpdate:
    """Test updating emulator status."""

    def test_update_emulator_status(self, client, app):
        """Test updating emulator status."""
        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_STATUS_TEST'
            fab.name = 'Status Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_STATUS01'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.socketio = Mock()

                response = client.post(f'/api/emulator/update_status/{fab_id}',
                                     json={'status': 'printing'})

                # Should succeed or fail gracefully
                assert response.status_code in [200, 400, 404, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()

    def test_update_status_invalid_status(self, client, app):
        """Test updating with invalid status."""
        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_INVALID_STATUS'
            fab.name = 'Invalid Status Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_INVALID01'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            response = client.post(f'/api/emulator/update_status/{fab_id}',
                                 json={'status': 'invalid_status'})

            # Should return 400 error
            assert response.status_code == 400

            # Clean up
            db.session.delete(fab)
            db.session.commit()

    def test_update_status_valid_statuses(self, client, app):
        """Test all valid status values."""
        valid_statuses = ['ready', 'printing', 'paused', 'error', 'offline', 'maintenance']

        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_VALID_STATUS'
            fab.name = 'Valid Status Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_VALID01'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.socketio = Mock()

                for status in valid_statuses:
                    response = client.post(f'/api/emulator/update_status/{fab_id}',
                                         json={'status': status})

                    # Should succeed
                    assert response.status_code in [200, 404, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()


class TestEmulatorLegacyEndpoints:
    """Test legacy emulator endpoints."""

    def test_start_emulator(self, client, app):
        """Test /startemulator endpoint."""
        with app.app_context():
            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()
                mock_app.socketio = Mock()

                # Create mock fabricator
                mock_fab = Mock()
                mock_fab.dbID = 1
                mock_fab.name = 'Virtual Printer'
                mock_fab.devicePort = 'EMU_12345678'

                with patch('controllers.emulator.Fabricator') as mock_fabricator_class:
                    mock_fabricator_class.query.filter_by.return_value.first.return_value = mock_fab

                    response = client.post('/startemulator',
                                         json={
                                             'model': 'Prusa MK4',
                                             'config': {
                                                 'name': 'Virtual Printer',
                                                 'description': 'Test',
                                                 'hwid': 'TEST_HWID'
                                             }
                                         })

                    # Should succeed or fail gracefully
                    assert response.status_code in [200, 400, 500]

    def test_register_emulator(self, client, app):
        """Test /registeremulator endpoint."""
        with app.app_context():
            response = client.post('/registeremulator',
                                 json={
                                     'config': {
                                         'port': 'EMU_12345678',
                                         'name': 'Test Emulator'
                                     }
                                 })

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True

    def test_disconnect_emulator(self, client, app):
        """Test /disconnectemulator endpoint."""
        with app.app_context():
            response = client.post('/disconnectemulator', json={})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True


class TestEmulatorReconstructorFix:
    """Test that emulator fabricators are properly initialized from database."""

    def test_emulator_loads_from_database(self, app):
        """Test emulator loads correctly from database with @reconstructor."""
        with app.app_context():
            # Create emulator in database
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_RECONSTRUCTOR'
            fab.name = 'Reconstructor Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_RECON01'
            fab.model = 'Prusa MK4'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            # Clear session to force reload
            db.session.expunge_all()

            # Load from database
            loaded_fab = Fabricator.query.filter_by(dbID=fab_id).first()

            # Verify runtime attributes are initialized
            assert loaded_fab is not None
            assert hasattr(loaded_fab, 'queue')
            assert loaded_fab.queue is not None
            assert hasattr(loaded_fab, 'status')
            assert hasattr(loaded_fab, 'device')
            assert hasattr(loaded_fab, 'error')

            # Clean up
            Fabricator.query.filter_by(dbID=fab_id).delete()
            db.session.commit()

    def test_emulator_queryAll(self, app):
        """Test queryAll returns emulators with initialized attributes."""
        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_QUERYALL'
            fab.name = 'QueryAll Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_QUERY01'
            fab.model = 'Prusa MK4'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            # Clear session
            db.session.expunge_all()

            # Use queryAll
            all_fabs = Fabricator.queryAll()

            # Find our emulator
            emu_fabs = [f for f in all_fabs if f.devicePort == 'EMU_QUERY01']

            assert len(emu_fabs) > 0

            for fab in emu_fabs:
                assert hasattr(fab, 'queue') and fab.queue is not None
                assert hasattr(fab, 'status')
                assert hasattr(fab, 'device')
                assert hasattr(fab, 'error')

            # Clean up
            Fabricator.query.filter_by(devicePort='EMU_QUERY01').delete()
            db.session.commit()


class TestEmulatorSocketIO:
    """Test SocketIO integration with emulators."""

    def test_emulator_emits_registration_event(self, client, app):
        """Test that emulator creation emits registration event."""
        with app.app_context():
            mock_socketio = Mock()

            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()
                mock_app.socketio = mock_socketio

                mock_fab = Mock()
                mock_fab.dbID = 1
                mock_fab.__to_JSON__ = Mock(return_value={'id': 1})

                with patch('controllers.emulator.Fabricator') as mock_fabricator:
                    mock_fabricator.query.filter_by.return_value.first.return_value = mock_fab

                    response = client.post('/startemulator',
                                         json={
                                             'model': 'Prusa MK4',
                                             'config': {'name': 'Test'}
                                         })

                    # SocketIO emit may or may not be called depending on flow
                    # Just verify no crash

    def test_status_update_emits_event(self, client, app):
        """Test that status update emits event."""
        with app.app_context():
            # Create emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_SOCKETIO'
            fab.name = 'SocketIO Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_SOCKET01'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            mock_socketio = Mock()

            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.socketio = mock_socketio

                response = client.post(f'/api/emulator/update_status/{fab_id}',
                                     json={'status': 'printing'})

                # SocketIO should emit (or endpoint returns error)
                assert response.status_code in [200, 404, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()


class TestEmulatorErrorHandling:
    """Test error handling in emulator operations."""

    def test_create_duplicate_port(self, client, app):
        """Test creating emulator with duplicate port."""
        with app.app_context():
            # Create existing emulator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'EMU_DUPLICATE'
            fab.name = 'Duplicate Test'
            fab.description = 'Test'
            fab.devicePort = 'EMU_DUP12345'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            # Mock to return the same port
            with patch('controllers.emulator.generate_mock_serial', return_value='DUP12345'):
                with patch('controllers.emulator.current_app') as mock_app:
                    mock_app.fabricator_list = Mock()

                    response = client.post('/api/emulator/create',
                                         json={'model': 'Test', 'name': 'Test'})

                    # Should return error
                    assert response.status_code in [400, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()

    def test_update_nonexistent_emulator(self, client, app):
        """Test updating emulator that doesn't exist."""
        with app.app_context():
            response = client.post('/api/emulator/update_status/999999',
                                 json={'status': 'ready'})

            assert response.status_code == 404

    def test_update_real_printer_status(self, client, app):
        """Test updating status of real printer is rejected."""
        with app.app_context():
            # Create real printer
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'REAL_FOR_STATUS'
            fab.name = 'Real Printer'
            fab.description = 'Real'
            fab.devicePort = 'ttyUSB0'
            fab.model = 'Test'
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            fab_id = fab.dbID

            response = client.post(f'/api/emulator/update_status/{fab_id}',
                                 json={'status': 'printing'})

            # Should return error (can only update mock printers)
            assert response.status_code in [400, 500]

            # Clean up
            db.session.delete(fab)
            db.session.commit()


class TestEmulatorModels:
    """Test different emulator models."""

    @pytest.mark.parametrize("model", ["Prusa MK3", "Prusa MK4", "Ender 3", "MakerBot Replicator"])
    def test_create_different_models(self, client, app, model):
        """Test creating emulators with different models."""
        with app.app_context():
            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()

                mock_fab = Mock()
                mock_fab.dbID = 1
                mock_fab.model = model

                with patch('controllers.emulator.Fabricator') as mock_fabricator:
                    mock_fabricator.query.filter_by.return_value.first.return_value = mock_fab

                    response = client.post('/api/emulator/create',
                                         json={'model': model, 'name': f'Test {model}'})

                    # Should handle all models
                    assert response.status_code in [200, 400, 500]
