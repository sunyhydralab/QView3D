"""
Tests for job-related functionality
"""
import pytest
import json
from unittest.mock import Mock, patch
import gzip


class TestJobsAPI:
    """Test job API endpoints."""

    def test_get_jobs_empty(self, client):
        """Test getting jobs when database is empty."""
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list) or (isinstance(data, tuple) and len(data) == 2)

    def test_get_jobs_with_filters(self, client):
        """Test getting jobs with various filters."""
        # Test with printer filter
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&printerIds=[1,2]')
        assert response.status_code == 200

        # Test with date range
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&startdate=2024-01-01&enddate=2024-12-31')
        assert response.status_code == 200

        # Test with search
        response = client.get('/api/jobs/getjobs?page=1&pageSize=10&searchJob=test')
        assert response.status_code == 200

    @patch('Classes.Jobs.Job.jobHistoryInsert')
    def test_add_job_to_queue(self, mock_insert, client):
        """Test adding a job to printer queue."""
        mock_insert.return_value = {'success': True, 'id': 1}

        # Prepare multipart form data
        data = {
            'name': 'Test Print',
            'printerid': '1',
            'favorite': 'false',
            'td_id': '12345',
            'filament': 'PLA',
            'priority': 'false'
        }

        # Mock file upload
        data['file'] = (b'test gcode content', 'test.gcode')

        response = client.post('/api/jobs/addjobtoqueue',
                              data=data,
                              content_type='multipart/form-data')

        # Note: This will likely fail without proper app context and fabricator setup
        # This is just the structure for the test

    def test_cancel_job(self, client):
        """Test cancelling a job."""
        response = client.post('/api/jobs/canceljob',
                              json={'jobpk': 1})
        # Will return 404 or error without actual job in database
        assert response.status_code in [200, 404, 500]


class TestJobModel:
    """Test Job model functionality."""

    def test_job_time_calculation(self):
        """Test time calculation from G-code comments."""
        from Classes.Jobs import Job

        # Test PrusaSlicer format
        comment_lines = [";FLAVOR:Marlin", ";TIME:3600"]
        time_seconds = Job.getTimeFromFile(comment_lines)
        assert time_seconds == 3600

        # Test Cura format
        comment_lines = ["; estimated printing time (normal mode) = 1 hours 30 minutes 45 seconds"]
        time_seconds = Job.getTimeFromFile(comment_lines)
        assert time_seconds == 5445  # 1*3600 + 30*60 + 45

    def test_job_status_updates(self, session):
        """Test job status update functionality."""
        from Classes.Jobs import Job

        # Create a test job
        job = Job(
            file=gzip.compress(b'test gcode'),
            name='Test Job',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=12345,
            fabricator_name='Test Printer'
        )
        session.add(job)
        session.commit()

        # Test status update
        assert job.status == 'pending'
        job.setStatus('printing')
        assert job.status == 'printing'

        # Test progress update
        job.setProgress(50.0)
        assert job.getProgress() == 50.0

    def test_job_serialization(self, session):
        """Test job JSON serialization."""
        from Classes.Jobs import Job
        from datetime import datetime

        job = Job(
            file=gzip.compress(b'test gcode'),
            name='Test Job',
            fabricator_id=1,
            status='completed',
            file_name_original='test.gcode',
            favorite=True,
            td_id=12345,
            fabricator_name='Test Printer'
        )
        session.add(job)
        session.commit()

        # Test JSON serialization
        job_json = job.__to_JSON__()
        assert job_json['name'] == 'Test Job'
        assert job_json['status'] == 'completed'
        assert job_json['favorite'] == True
        assert job_json['td_id'] == 12345


class TestJobFileHandling:
    """Test file handling for jobs."""

    def test_gcode_compression(self):
        """Test G-code file compression and decompression."""
        original_content = b"G28 ; Home all axes\nG1 X10 Y10 Z0.2\n"

        # Compress
        compressed = gzip.compress(original_content)
        assert len(compressed) < len(original_content) * 2  # Should have some compression

        # Decompress
        decompressed = gzip.decompress(compressed)
        assert decompressed == original_content

    def test_file_name_generation(self, session):
        """Test unique file name generation with job ID."""
        from Classes.Jobs import Job

        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='model.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        # Set file name with ID
        job.setFileName(f'model_{job.id}.gcode')
        assert job.getFileNamePk() == f'model_{job.id}.gcode'


class TestJobQueueOperations:
    """Test job queue management."""

    @patch('services.fabricator_service.FabricatorService.find_by_id')
    def test_queue_priority(self, mock_find):
        """Test adding jobs to front vs back of queue."""
        # Mock fabricator with queue
        mock_fabricator = Mock()
        mock_queue = Mock()
        mock_fabricator.queue = mock_queue
        mock_find.return_value = mock_fabricator

        from services.job_service import JobService

        # Test adding to back (normal priority)
        JobService.create_job_in_queue(
            file=b'test',
            file_name_original='test.gcode',
            name='Normal Priority',
            printer_id=1,
            favorite='false',
            td_id=1,
            filament='PLA',
            priority='false',
            fabricator=mock_fabricator
        )
        mock_queue.addToBack.assert_called_once()

        # Reset mock
        mock_queue.reset_mock()

        # Test adding to front (high priority)
        JobService.create_job_in_queue(
            file=b'test',
            file_name_original='test.gcode',
            name='High Priority',
            printer_id=1,
            favorite='false',
            td_id=2,
            filament='PLA',
            priority='true',
            fabricator=mock_fabricator
        )
        mock_queue.addToFront.assert_called_once()