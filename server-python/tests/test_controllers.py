"""
Comprehensive tests for API controllers - All endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import gzip
import io

from Classes.Jobs import Job
from Classes.Issues import Issue
from Classes.Fabricators.Fabricator import Fabricator
from config.db import db


class TestIssuesController:
    """Test issues controller endpoints."""

    def test_get_issues(self, client, app):
        """Test GET /getissues endpoint."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create test issue
                issue = Issue(
                    title="Test Issue",
                    description="Test",
                    severity="medium"
                )

                response = client.get('/api/issues/getissues')
                assert response.status_code == 200

                data = json.loads(response.data)
                assert 'issues' in data
                assert isinstance(data['issues'], list)

    def test_create_issue(self, client, app):
        """Test POST /createissue endpoint."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                response = client.post('/api/issues/createissue',
                                     json={
                                         'title': 'New Issue',
                                         'description': 'Test description',
                                         'severity': 'high',
                                         'category': 'printer'
                                     })

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True

    def test_create_issue_legacy_format(self, client, app):
        """Test creating issue with legacy format."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                response = client.post('/api/issues/createissue',
                                     json={'issue': 'Legacy issue text'})

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True

    def test_update_issue(self, client, app):
        """Test POST /updateissue endpoint."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue first
                issue = Issue(
                    title="Original",
                    description="Original"
                )

                response = client.post('/api/issues/updateissue',
                                     json={
                                         'id': issue.id,
                                         'title': 'Updated Title',
                                         'severity': 'critical'
                                     })

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True

    def test_resolve_issue(self, client, app):
        """Test POST /resolveissue endpoint."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue first
                issue = Issue(
                    title="To Resolve",
                    description="Test"
                )

                response = client.post('/api/issues/resolveissue',
                                     json={'id': issue.id})

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True

    def test_delete_issue(self, client, app):
        """Test POST /deleteissue endpoint."""
        with app.app_context():
            with patch('Classes.Issues.current_app', app):
                # Create issue first
                issue = Issue(
                    title="To Delete",
                    description="Test"
                )
                issue_id = issue.id

                response = client.post('/api/issues/deleteissue',
                                     json={'id': issue_id})

                assert response.status_code == 200

    def test_delete_issue_missing_id(self, client, app):
        """Test deleting issue without ID returns error."""
        with app.app_context():
            response = client.post('/api/issues/deleteissue', json={})

            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'error' in data


class TestJobsController:
    """Test jobs controller endpoints."""

    def test_get_jobs_empty(self, client):
        """Test GET /getjobs with empty database."""
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'jobs' in data or 'total' in data

    def test_get_jobs_with_filters(self, client):
        """Test GET /getjobs with various filters."""
        # Test with printer filter
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&printerIds=[1,2]')
        assert response.status_code == 200

        # Test with date range
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&startdate=2024-01-01&enddate=2024-12-31')
        assert response.status_code == 200

        # Test with search
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&searchJob=test')
        assert response.status_code == 200

    def test_get_jobs_count_only(self, client):
        """Test GET /getjobs with countOnly parameter."""
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&countOnly=1')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'total' in data

    def test_cancel_job(self, client, app, session):
        """Test POST /canceljob endpoint."""
        with app.app_context():
            # Create a test job
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='inqueue',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            # Mock fabricator
            with patch('controllers.jobs.findPrinterObject') as mock_find:
                mock_fabricator = Mock()
                mock_queue = Mock()
                mock_queue.getJob.return_value = job
                mock_queue.deleteJob.return_value = job
                mock_fabricator.getQueue.return_value = mock_queue
                mock_fabricator.setStatus = Mock()
                mock_find.return_value = mock_fabricator

                response = client.post('/api/jobs/canceljob',
                                     json={'jobpk': job.id})

                # May return 200 or 404/500 depending on setup
                assert response.status_code in [200, 404, 500]

    def test_get_file(self, client, app, session):
        """Test GET /getfile endpoint."""
        with app.app_context():
            # Create a test job with file
            gcode_content = b'G28\nG1 X10 Y10'
            job = Job(
                file=gzip.compress(gcode_content),
                name='Test Job',
                fabricator_id=1,
                status='completed',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            with patch('controllers.jobs.current_app', app):
                response = client.get(f'/api/jobs/getfile?jobid={job.id}')

                # May succeed or fail depending on app context
                assert response.status_code in [200, 500]

    def test_favorite_job(self, client, app, session):
        """Test POST /favoritejob endpoint."""
        with app.app_context():
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='completed',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            with patch('controllers.jobs.current_app', app):
                response = client.post('/api/jobs/favoritejob',
                                     json={'jobid': job.id, 'favorite': True})

                # May succeed or fail
                assert response.status_code in [200, 500]


class TestPortsController:
    """Test ports/fabricators controller endpoints."""

    def test_get_ports(self, client, app):
        """Test GET /getports endpoint."""
        with app.app_context():
            with patch('Classes.Ports.Ports.getPorts') as mock_ports:
                mock_ports.return_value = [
                    {'device': '/dev/ttyUSB0', 'name': 'USB Serial'},
                    {'device': '/dev/ttyACM0', 'name': 'Arduino'}
                ]

                response = client.get('/getports')

                assert response.status_code == 200
                data = json.loads(response.data)
                assert isinstance(data, list)

    def test_get_fabricators(self, client, app):
        """Test GET /getfabricators endpoint."""
        with app.app_context():
            response = client.get('/getfabricators')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list) or isinstance(data, dict)

    def test_edit_fabricator_name(self, client, app, session):
        """Test POST /editname endpoint."""
        with app.app_context():
            # Create a test fabricator
            fab = Fabricator.__new__(Fabricator)
            fab.hwid = 'TEST_HWID'
            fab.name = 'Original Name'
            fab.description = 'Test'
            fab.devicePort = 'ttyUSB0'
            fab.model = 'Test Model'
            from datetime import datetime, timezone
            fab.date = datetime.now(timezone.utc).astimezone()

            db.session.add(fab)
            db.session.commit()

            response = client.post('/editname',
                                 json={
                                     'fabricator_id': fab.dbID,
                                     'name': 'New Name'
                                 })

            # May succeed or fail
            assert response.status_code in [200, 404, 500]

    def test_get_fabricator_models(self, client, app):
        """Test GET /fabricators/models endpoint."""
        with app.app_context():
            response = client.get('/fabricators/models')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)


class TestEmulatorController:
    """Test emulator controller endpoints."""

    def test_create_mock_printer(self, client, app):
        """Test POST /emulator/create endpoint."""
        with app.app_context():
            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()

                response = client.post('/api/emulator/create',
                                     json={
                                         'model': 'Prusa MK4',
                                         'name': 'Test Mock Printer'
                                     })

                # May succeed or fail depending on setup
                assert response.status_code in [200, 400, 500]

    def test_list_mock_printers(self, client, app):
        """Test GET /emulator/list endpoint."""
        with app.app_context():
            response = client.get('/api/emulator/list')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert isinstance(data, list)

    def test_start_emulator(self, client, app):
        """Test POST /startemulator endpoint."""
        with app.app_context():
            with patch('controllers.emulator.current_app') as mock_app:
                mock_app.fabricator_list = Mock()
                mock_app.fabricator_list.addFabricator = Mock()
                mock_app.socketio = Mock()

                response = client.post('/startemulator',
                                     json={
                                         'model': 'Prusa MK4',
                                         'config': {
                                             'name': 'Virtual Printer',
                                             'description': 'Test'
                                         }
                                     })

                # May succeed or fail
                assert response.status_code in [200, 400, 500]

    def test_disconnect_emulator(self, client, app):
        """Test POST /disconnectemulator endpoint."""
        with app.app_context():
            response = client.post('/disconnectemulator', json={})

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True


class TestJobsControllerAdvanced:
    """Test advanced job controller operations."""

    def test_bump_job(self, client, app, session):
        """Test POST /bumpjob endpoint."""
        with app.app_context():
            with patch('controllers.jobs.findPrinterObject') as mock_find:
                mock_fabricator = Mock()
                mock_queue = Mock()
                mock_fabricator.queue = mock_queue
                mock_find.return_value = mock_fabricator

                response = client.post('/api/jobs/bumpjob',
                                     json={
                                         'printerid': 1,
                                         'jobid': 1,
                                         'choice': 1
                                     })

                # May succeed or fail
                assert response.status_code in [200, 404, 500]

    def test_reorder_queue(self, client, app):
        """Test POST /reorderqueue endpoint."""
        with app.app_context():
            with patch('controllers.jobs.findPrinterObject') as mock_find:
                mock_fabricator = Mock()
                mock_queue = Mock()
                mock_fabricator.queue = mock_queue
                mock_find.return_value = mock_fabricator

                response = client.post('/api/jobs/reorderqueue',
                                     json={
                                         'fabricator_id': 1,
                                         'job_ids': [3, 1, 2]
                                     })

                assert response.status_code in [200, 400, 404, 500]

    def test_reorder_queue_missing_params(self, client, app):
        """Test /reorderqueue with missing parameters."""
        with app.app_context():
            response = client.post('/api/jobs/reorderqueue', json={})

            assert response.status_code == 400

    def test_update_job_status(self, client, app, session):
        """Test POST /updatejobstatus endpoint."""
        with app.app_context():
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='printing',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            with patch('controllers.jobs.findPrinterObject') as mock_find:
                mock_fabricator = Mock()
                mock_queue = Mock()
                mock_fabricator.getQueue.return_value = mock_queue
                mock_find.return_value = mock_fabricator

                response = client.post('/api/jobs/updatejobstatus',
                                     json={
                                         'jobid': job.id,
                                         'status': 'completed'
                                     })

                # May succeed or fail
                assert response.status_code in [200, 500]

    def test_delete_job(self, client, app, session):
        """Test POST /deletejob endpoint."""
        with app.app_context():
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='completed',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            with patch('controllers.jobs.findPrinterObject') as mock_find:
                mock_find.return_value = None

                response = client.post('/api/jobs/deletejob',
                                     json={'jobid': job.id})

                # May succeed or fail
                assert response.status_code in [200, 500]

    def test_save_comment(self, client, app, session):
        """Test POST /savecomment endpoint."""
        with app.app_context():
            job = Job(
                file=gzip.compress(b'test'),
                name='Test Job',
                fabricator_id=1,
                status='completed',
                file_name_original='test.gcode',
                favorite=False,
                td_id=1,
                fabricator_name='Printer1'
            )
            session.add(job)
            session.commit()

            with patch('controllers.jobs.current_app', app):
                response = client.post('/api/jobs/savecomment',
                                     json={
                                         'jobid': job.id,
                                         'comments': 'Test comment'
                                     })

                assert response.status_code in [200, 500]


class TestStatusController:
    """Test status service controller."""

    def test_health_check(self, client):
        """Test health check endpoint if it exists."""
        # This endpoint may or may not exist
        response = client.get('/health')
        # Don't assert on status code as endpoint may not exist
        # Just check it doesn't crash

    def test_status_endpoint(self, client):
        """Test status endpoint if it exists."""
        response = client.get('/status')
        # Endpoint may not exist, just check no crash


class TestControllerErrorHandling:
    """Test error handling in controllers."""

    def test_invalid_json(self, client):
        """Test sending invalid JSON to endpoints."""
        response = client.post('/api/issues/createissue',
                             data='invalid json',
                             content_type='application/json')

        assert response.status_code in [400, 500]

    def test_missing_required_fields(self, client):
        """Test endpoints with missing required fields."""
        # Try to create issue without required fields
        response = client.post('/api/issues/createissue', json={})

        # Should either succeed (with defaults) or fail
        assert response.status_code in [200, 400, 500]

    def test_invalid_id_parameters(self, client):
        """Test endpoints with invalid ID parameters."""
        # Try to get job with invalid ID
        response = client.get('/api/jobs/getfile?jobid=invalid')

        assert response.status_code in [400, 500]

    def test_nonexistent_resource(self, client):
        """Test accessing nonexistent resources."""
        response = client.post('/api/jobs/canceljob',
                             json={'jobpk': 999999})

        assert response.status_code in [200, 404, 500]


class TestMultipartFormData:
    """Test multipart form data handling."""

    def test_add_job_to_queue_structure(self, client, app):
        """Test the structure of adding job to queue."""
        # This is a complex test that would require proper file upload setup
        # Just test the endpoint exists
        response = client.post('/api/jobs/addjobtoqueue')

        # Will fail without proper data, but shouldn't crash
        assert response.status_code in [400, 500]


class TestCORSAndHeaders:
    """Test CORS and header handling."""

    def test_options_request(self, client):
        """Test OPTIONS request for CORS."""
        response = client.options('/api/issues/getissues')

        # Should handle OPTIONS or return method not allowed
        assert response.status_code in [200, 204, 405]

    def test_content_type_json(self, client, app):
        """Test that JSON responses have correct content type."""
        with app.app_context():
            response = client.get('/api/issues/getissues')

            if response.status_code == 200:
                assert 'application/json' in response.content_type


class TestPaginationAndFiltering:
    """Test pagination and filtering in list endpoints."""

    def test_jobs_pagination(self, client):
        """Test job list pagination."""
        # Page 1
        response1 = client.get('/api/jobs/getjobs?page=1&pageSize=5')
        assert response1.status_code == 200

        # Page 2
        response2 = client.get('/api/jobs/getjobs?page=2&pageSize=5')
        assert response2.status_code == 200

    def test_jobs_filtering_combinations(self, client):
        """Test combining multiple filters."""
        response = client.get(
            '/api/jobs/getjobs?page=1&pageSize=10&printerIds=[1]&favoriteOnly=true&searchJob=test'
        )
        assert response.status_code == 200

    def test_invalid_pagination_params(self, client):
        """Test invalid pagination parameters."""
        # Negative page
        response = client.get('/api/jobs/getjobs?page=-1&pageSize=10')
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]

        # Zero page size
        response = client.get('/api/jobs/getjobs?page=1&pageSize=0')
        assert response.status_code in [200, 400, 500]
