"""
Comprehensive tests for Queue class - thread-safe job queue management
"""
import pytest
import threading
import time
from unittest.mock import Mock, patch
import gzip

from Classes.Queue import Queue
from Classes.Jobs import Job


class TestQueueBasicOperations:
    """Test basic queue operations."""

    def test_queue_initialization(self):
        """Test queue is initialized correctly."""
        queue = Queue()
        assert len(queue) == 0
        assert hasattr(queue, '_lock')
        assert hasattr(queue, '_condition')
        assert queue._version == 0

    def test_add_to_back(self, session):
        """Test adding job to back of queue."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test gcode'),
            name='Test Job',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            result = queue.addToBack(job)

        assert result is True
        assert len(queue) == 1
        assert queue[0] == job
        assert queue._version == 1

    def test_add_to_front(self, session):
        """Test adding job to front of queue."""
        queue = Queue()
        job1 = Job(
            file=gzip.compress(b'test gcode 1'),
            name='Job 1',
            fabricator_id=1,
            status='pending',
            file_name_original='test1.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        job2 = Job(
            file=gzip.compress(b'test gcode 2'),
            name='Job 2',
            fabricator_id=1,
            status='pending',
            file_name_original='test2.gcode',
            favorite=False,
            td_id=2,
            fabricator_name='Printer1'
        )
        session.add_all([job1, job2])
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job1)
            queue.addToFront(job2)

        assert len(queue) == 2
        assert queue[0] == job2
        assert queue[1] == job1

    def test_add_duplicate_job(self, session):
        """Test that adding duplicate job returns False."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            result1 = queue.addToBack(job)
            result2 = queue.addToBack(job)

        assert result1 is True
        assert result2 is False
        assert len(queue) == 1

    def test_add_to_front_with_printing_job(self, session):
        """Test adding to front when first job is printing."""
        queue = Queue()
        printing_job = Job(
            file=gzip.compress(b'printing'),
            name='Printing Job',
            fabricator_id=1,
            status='printing',
            file_name_original='printing.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        new_job = Job(
            file=gzip.compress(b'new'),
            name='New Job',
            fabricator_id=1,
            status='pending',
            file_name_original='new.gcode',
            favorite=False,
            td_id=2,
            fabricator_name='Printer1'
        )
        session.add_all([printing_job, new_job])
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(printing_job)
            queue.addToFront(new_job)

        assert len(queue) == 2
        assert queue[0] == printing_job
        assert queue[1] == new_job

    def test_remove_job(self, session):
        """Test removing job from queue."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            removed = queue.removeJob()

        assert removed == job
        assert len(queue) == 0

    def test_remove_from_empty_queue(self):
        """Test removing from empty queue returns None."""
        queue = Queue()
        removed = queue.removeJob()
        assert removed is None


class TestQueueSearch:
    """Test queue search operations."""

    def test_get_next(self, session):
        """Test getting next job without removing."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            next_job = queue.getNext()

        assert next_job == job
        assert len(queue) == 1

    def test_get_next_empty_queue(self):
        """Test getting next from empty queue."""
        queue = Queue()
        next_job = queue.getNext()
        assert next_job is None

    def test_get_job_by_id(self, session):
        """Test finding job by ID."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            found = queue.getJobById(job.id)

        assert found == job

    def test_get_job_by_id_not_found(self, session):
        """Test finding non-existent job returns None."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            found = queue.getJobById(999999)

        assert found is None

    def test_job_exists(self, session):
        """Test checking if job exists in queue."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)

        assert queue.jobExists(job.id) is True
        assert queue.jobExists(999999) is False


class TestQueueReordering:
    """Test queue reordering operations."""

    def test_bump_up(self, session):
        """Test bumping job up in queue."""
        queue = Queue()
        job1 = Job(
            file=gzip.compress(b'job1'),
            name='Job 1',
            fabricator_id=1,
            status='pending',
            file_name_original='job1.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        job2 = Job(
            file=gzip.compress(b'job2'),
            name='Job 2',
            fabricator_id=1,
            status='pending',
            file_name_original='job2.gcode',
            favorite=False,
            td_id=2,
            fabricator_name='Printer1'
        )
        session.add_all([job1, job2])
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job1)
            queue.addToBack(job2)
            queue.bump(True, job2.id)

        assert queue[0] == job2
        assert queue[1] == job1

    def test_bump_down(self, session):
        """Test bumping job down in queue."""
        queue = Queue()
        job1 = Job(
            file=gzip.compress(b'job1'),
            name='Job 1',
            fabricator_id=1,
            status='pending',
            file_name_original='job1.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        job2 = Job(
            file=gzip.compress(b'job2'),
            name='Job 2',
            fabricator_id=1,
            status='pending',
            file_name_original='job2.gcode',
            favorite=False,
            td_id=2,
            fabricator_name='Printer1'
        )
        session.add_all([job1, job2])
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job1)
            queue.addToBack(job2)
            queue.bump(False, job1.id)

        assert queue[0] == job2
        assert queue[1] == job1

    def test_bump_extreme_to_front(self, session):
        """Test bumping job to front of queue."""
        queue = Queue()
        jobs = []
        for i in range(3):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            for job in jobs:
                queue.addToBack(job)
            queue.bumpExtreme(True, jobs[2].id, 1)

        assert queue[0] == jobs[2]

    def test_bump_extreme_to_back(self, session):
        """Test bumping job to back of queue."""
        queue = Queue()
        jobs = []
        for i in range(3):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            for job in jobs:
                queue.addToBack(job)
            queue.bumpExtreme(False, jobs[0].id, 1)

        assert queue[2] == jobs[0]

    def test_reorder(self, session):
        """Test reordering entire queue."""
        queue = Queue()
        jobs = []
        for i in range(3):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            for job in jobs:
                queue.addToBack(job)

            # Reorder: 2, 0, 1
            new_order = [jobs[2].id, jobs[0].id, jobs[1].id]
            queue.reorder(new_order)

        assert queue[0] == jobs[2]
        assert queue[1] == jobs[0]
        assert queue[2] == jobs[1]

    def test_delete_job(self, session):
        """Test deleting specific job from queue."""
        queue = Queue()
        jobs = []
        for i in range(3):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        with patch('Classes.Queue.current_app'):
            for job in jobs:
                queue.addToBack(job)

            deleted = queue.deleteJob(jobs[1].id, 1)

        assert deleted == jobs[1]
        assert len(queue) == 2
        assert jobs[1] not in queue


class TestQueueThreadSafety:
    """Test thread-safety of queue operations."""

    def test_concurrent_additions(self, session):
        """Test multiple threads adding jobs concurrently."""
        queue = Queue()
        jobs = []
        for i in range(10):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        def add_jobs(start, end):
            with patch('Classes.Queue.current_app', None):
                for i in range(start, end):
                    queue.addToBack(jobs[i])

        threads = [
            threading.Thread(target=add_jobs, args=(0, 5)),
            threading.Thread(target=add_jobs, args=(5, 10))
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(queue) == 10

    def test_wait_for_job_with_timeout(self):
        """Test wait_for_job with timeout."""
        queue = Queue()

        def add_job_later():
            time.sleep(0.1)
            job = Mock()
            job.fabricator_id = 1
            with patch('Classes.Queue.current_app', None):
                queue.addToBack(job)

        thread = threading.Thread(target=add_job_later)
        thread.start()

        job = queue.wait_for_job(timeout=1.0)
        thread.join()

        assert job is not None

    def test_wait_for_job_timeout_expires(self):
        """Test wait_for_job when timeout expires."""
        queue = Queue()
        job = queue.wait_for_job(timeout=0.1)
        assert job is None


class TestQueueSerialization:
    """Test queue serialization."""

    def test_convert_to_json(self, session):
        """Test converting queue to JSON."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test Job',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            json_data = queue.convertQueueToJson()

        assert isinstance(json_data, list)
        assert len(json_data) == 1
        assert json_data[0]['name'] == 'Test Job'

    def test_list_conversion(self, session):
        """Test __list__ method."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test Job',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            job_list = queue.__list__()

        assert isinstance(job_list, list)
        assert len(job_list) == 1


class TestQueueStatusManagement:
    """Test queue status management."""

    def test_set_to_in_queue(self, session):
        """Test setting all jobs to 'inqueue' status."""
        queue = Queue()
        jobs = []
        for i in range(3):
            job = Job(
                file=gzip.compress(f'job{i}'.encode()),
                name=f'Job {i}',
                fabricator_id=1,
                status='pending',
                file_name_original=f'job{i}.gcode',
                favorite=False,
                td_id=i,
                fabricator_name='Printer1'
            )
            jobs.append(job)
        session.add_all(jobs)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            for job in jobs:
                queue.addToBack(job)

            queue.setToInQueue()

        for job in queue:
            assert job.status == 'inqueue'


class TestQueueEdgeCases:
    """Test edge cases and error handling."""

    def test_bump_nonexistent_job(self, session):
        """Test bumping a job that doesn't exist."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)
            queue.bump(True, 999999)

        # Should not crash, just print message
        assert len(queue) == 1

    def test_delete_nonexistent_job(self):
        """Test deleting a job that doesn't exist."""
        queue = Queue()

        with patch('Classes.Queue.current_app'):
            result = queue.deleteJob(999999, 1)

        assert result == "Job not found in queue."

    def test_version_increment(self, session):
        """Test that version increments on modifications."""
        queue = Queue()
        job = Job(
            file=gzip.compress(b'test'),
            name='Test',
            fabricator_id=1,
            status='pending',
            file_name_original='test.gcode',
            favorite=False,
            td_id=1,
            fabricator_name='Printer1'
        )
        session.add(job)
        session.commit()

        initial_version = queue._version

        with patch('Classes.Queue.current_app', None):
            queue.addToBack(job)

        assert queue._version == initial_version + 1
