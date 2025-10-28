"""
New threading architecture for QView3D fabricator management.

Implements:
1. IdleMonitorThread - Shared thread that monitors all idle printers
2. PrintWorkerThread - Dedicated thread spawned per active print job

This replaces the old "one thread per fabricator forever" model with
a more efficient "shared idle monitor + per-print worker threads" model.
"""

import time
import threading
from threading import Thread
from typing import Dict, List, Callable
from services.app_service import current_app


class IdleMonitorThread(Thread):
    """
    Shared thread that monitors all idle fabricators.

    Responsibilities:
    - Monitor temperature for idle printers (batched reads every 10 seconds)
    - Watch for new jobs added to fabricator queues
    - Trigger print start when jobs become available
    - Check printer connectivity periodically
    - Spawn PrintWorkerThread when print job starts

    This single thread replaces N per-fabricator threads when printers are idle,
    dramatically reducing resource usage.
    """

    def __init__(self, fabricator_list, app):
        """
        Initialize idle monitor thread.

        :param fabricator_list: Reference to FabricatorList instance
        :param app: QViewApp instance for app context
        """
        super().__init__(daemon=True, name="IdleMonitorThread")
        self.fabricator_list = fabricator_list
        self.app = app
        self.terminated = False
        self._sleep_interval = 2.0  # Check every 2 seconds
        self._temp_check_interval = 10.0  # Temperature check every 10 seconds
        self._last_temp_check = 0

    def run(self):
        """Main loop for idle monitoring."""
        with self.app.app_context():
            while not self.terminated:
                try:
                    current_time = time.time()

                    # Get list of idle fabricators (not currently printing)
                    idle_fabricators = [
                        fab for fab in self.fabricator_list.fabricators
                        if not self._is_printing(fab)
                    ]

                    # Periodic temperature monitoring for idle printers
                    if current_time - self._last_temp_check >= self._temp_check_interval:
                        self._monitor_temperatures(idle_fabricators)
                        self._last_temp_check = current_time

                    # Check each idle fabricator for new jobs in queue
                    for fabricator in idle_fabricators:
                        self._check_for_job_start(fabricator)

                    # Sleep until next check
                    time.sleep(self._sleep_interval)

                except Exception as e:
                    self.app.handle_errors_and_logging(e)
                    time.sleep(self._sleep_interval)

    def _is_printing(self, fabricator) -> bool:
        """
        Check if fabricator is currently printing.

        :param fabricator: Fabricator instance
        :return: True if printing, False otherwise
        """
        # Check status first - this is the most reliable indicator
        status = getattr(fabricator, 'status', 'unknown')
        if status == 'printing':
            return True

        # Also check if there's an active print thread for this fabricator
        if hasattr(self.fabricator_list, 'active_print_threads'):
            return fabricator.dbID in self.fabricator_list.active_print_threads

        return False

    def _monitor_temperatures(self, idle_fabricators):
        """
        Monitor temperatures for all idle printers (batched operation).

        :param idle_fabricators: List of idle Fabricator instances
        """
        from Classes.Fabricators.Printers.Printer import Printer

        for fabricator in idle_fabricators:
            try:
                # Only check temperature for actual Printer devices
                if not isinstance(getattr(fabricator, 'device', None), Printer):
                    continue

                # Skip if device not connected
                if not fabricator.device or not hasattr(fabricator.device, 'serialConnection'):
                    continue

                if not fabricator.device.serialConnection or not fabricator.device.serialConnection.is_open:
                    continue

                # Double-check fabricator is not printing (safety check)
                if getattr(fabricator, 'status', '') == 'printing':
                    continue

                # Read temperature (non-blocking with timeout)
                try:
                    fabricator.device.handleTempLine(fabricator.device.serialConnection.read())
                except Exception as e:
                    # Temperature read failed, printer may be disconnected
                    if getattr(fabricator, 'status', None) != 'offline':
                        fabricator.status = 'offline'

            except Exception:
                pass  # Temperature monitoring is best-effort

    def _check_for_job_start(self, fabricator):
        """
        Check if fabricator has a job ready to start.
        If so, spawn PrintWorkerThread.

        :param fabricator: Fabricator instance to check
        """
        try:
            # Check if queue has jobs
            if not hasattr(fabricator, 'queue') or len(fabricator.queue) == 0:
                return

            # Get next job (thread-safe)
            next_job = fabricator.queue.getNext()
            if not next_job:
                return

            # Check if job is ready to print (status must be 'inqueue', not already printing)
            if next_job.status != 'inqueue':
                return

            # Check if fabricator is in a ready state
            fabricator_status = getattr(fabricator, 'status', 'unknown')
            if fabricator_status not in ['ready', 'offline']:  # offline printers can try to reconnect
                return

            # All conditions met - start the print job!
            self.fabricator_list.start_print_job(fabricator, next_job)

        except Exception as e:
            self.app.handle_errors_and_logging(e)

    def stop(self):
        """Stop the idle monitor thread gracefully."""
        self.terminated = True


class PrintWorkerThread(Thread):
    """
    Dedicated thread for executing a single print job.

    Spawned when a print job starts, terminated when print completes/fails.
    This allows isolation of print execution and better error handling.

    Each active print gets its own dedicated worker thread that:
    - Calls fabricator.begin() to start the print
    - Executes device.parseGcode() to stream G-code
    - Monitors print progress
    - Handles completion and errors
    - Self-terminates when done
    """

    def __init__(self, fabricator, job, fabricator_list, app):
        """
        Initialize print worker thread.

        :param fabricator: Fabricator instance executing the print
        :param job: Job instance to print
        :param fabricator_list: Reference to FabricatorList for callbacks
        :param app: QViewApp instance for app context
        """
        super().__init__(daemon=True, name=f"PrintWorker-{fabricator.name}-Job{job.id}")
        self.fabricator = fabricator
        self.job = job
        self.fabricator_list = fabricator_list
        self.app = app
        self.terminated = False

    def run(self):
        """Execute the print job."""
        # CRITICAL FIX: Wrap entire operation in app context, including finally block
        with self.app.app_context():
            try:
                # Update job status to printing
                self.job.status = 'printing'
                from config.db import db
                db.session.commit()

                # Update fabricator status
                self.fabricator.status = 'printing'

                # Start the print (this calls device.parseGcode() which is synchronous/blocking)
                success = self.fabricator.begin()

                # Determine final status
                if success:
                    final_status = 'complete'
                else:
                    final_status = 'error'
                    error_msg = getattr(self.fabricator, 'error', 'Unknown error')
                    print(f"Print failed - Job {self.job.id}: {error_msg}")

                # Update job status
                self.job.status = final_status
                db.session.commit()

                # Notify fabricator list of completion
                self.fabricator_list.print_completed(self.fabricator, success)

            except Exception as e:
                print(f"Print error - Job {self.job.id}: {e}")
                self.app.handle_errors_and_logging(e)

                # Mark job as error
                try:
                    self.job.status = 'error'
                    from config.db import db
                    db.session.commit()
                except Exception:
                    pass  # Continue anyway - we still need to notify and clean up

                # Notify of failure
                self.fabricator_list.print_completed(self.fabricator, False)

            finally:
                # Remove job from queue (NOW INSIDE APP CONTEXT)
                try:
                    self.fabricator.queue.removeJob()
                except Exception:
                    pass  # Queue cleanup is best-effort

                # Reset fabricator status to ready
                self.fabricator.status = 'ready'

    def stop(self):
        """
        Request thread termination (not forceful).
        Note: Print operations are blocking, so this may not take effect immediately.
        """
        self.terminated = True
