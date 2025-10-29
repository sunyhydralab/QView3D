from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy import inspect

from Classes.Fabricators.Printers.Printer import Printer
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Jobs import Job
from Classes.Queue import Queue
from Classes.FabricatorThreading import IdleMonitorThread, PrintWorkerThread
import time
from services.app_service import current_app as app
# Removed tabs import - no longer needed
from config.db import db

class FabricatorList:
    def __init__(self, passed_app=app):
        """
        Initialize FabricatorList with new threading architecture.

        New Architecture:
        - Single IdleMonitorThread monitors all idle printers
        - PrintWorkerThread spawned per active print job
        - No permanent per-fabricator threads

        Old Architecture (REMOVED):
        - One FabricatorThread per fabricator (always running)
        """
        self.app = passed_app
        with self.app.app_context():
            # Initialize fabricator table
            if not inspect(db.engine).has_table('Fabricators') or not Fabricator.metadata.tables:
                Fabricator.metadata.create_all(db.engine)

            # Query fabricators
            self.fabricators = Fabricator.queryAll()

            # NEW: Single idle monitor thread for all fabricators
            self.idle_monitor = IdleMonitorThread(self, self.app)

            # NEW: Dict of active print threads {fabricator_id: PrintWorkerThread}
            self.active_print_threads = {}

            # Restore queues from database
            self.restore_queues_from_database()

            # Connect devices for fabricators that have real hardware
            for fabricator in self.fabricators:
                if hasattr(fabricator, 'device') and fabricator.device is not None:
                    try:
                        fabricator.device.connect()
                    except Exception as e:
                        print(f"Error connecting fabricator {fabricator.name}: {e}")
                        fabricator.status = 'offline'

            # Start the idle monitor thread
            self.idle_monitor.start()

    def __iter__(self):
        return iter(self.fabricators)

    def __len__(self):
        return len(self.fabricators)

    def __getitem__(self, key):
        return self.fabricators[key]

    def __to_JSON__(self):
        """
        Convert the FabricatorList to a JSON object that can be sent to the frontend
        :rtype: dict
        """
        fab_list = []
        for fabricator in self:
            fab_list.append(fabricator.__to_JSON__())
        thread_list = []
        for thread in self.fabricator_threads:
            thread_list.append(thread.__to_JSON__())
        return {
            "fabricators": fab_list,
            "fabricator_threads": thread_list,
            "ping_thread": self.ping_thread,
            "app": self.app,
        }

    def teardown(self):
        """
        Stop all threads gracefully.

        NEW: Stop idle monitor and all active print threads
        OLD: Stopped per-fabricator threads
        """
        # Stop idle monitor
        if hasattr(self, 'idle_monitor') and self.idle_monitor:
            self.idle_monitor.stop()
            self.idle_monitor.join(timeout=5)

        # Stop all active print threads
        if hasattr(self, 'active_print_threads'):
            for fabricator_id, thread in list(self.active_print_threads.items()):
                thread.stop()
                thread.join(timeout=5)
            self.active_print_threads.clear()

    def addFabricator(self, serialPortName: str, name: str = ""):
        """
        add a fabricator to the list, and to the database, then start a thread for it
        :param str serialPortName: the name of the serial port to add
        :param str name: the name of the fabricator to add
        """
        # Handle emulated printers (EMU_ prefix)
        if serialPortName.startswith('EMU_'):
            # Check if emulator already exists in database
            dbFab = Fabricator.query.filter_by(devicePort=serialPortName).first()
            if dbFab:
                raise Exception(f"Emulated printer already exists with port {serialPortName}")

            # Create emulated printer directly in database (no real serial port)
            newFab = Fabricator(devicePort=serialPortName, name=name)
            newFab.status = "ready"
            self.fabricators.append(newFab)
            db.session.add(newFab)
            db.session.commit()
            # Note: Emulated printers don't get a thread (no real device to monitor)
            return

        # Handle real printers with actual serial ports
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        if serialPort is None:
            raise Exception(f"Serial port {serialPortName} not found")

        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in self if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        newFab: Fabricator | None = None
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                err = Exception(f"This fabricator is already registered as {dbFab.getName()}")
                app.handle_errors_and_logging(err, getattr(listFab.device, 'logger', None) if listFab.device else None)
                raise err
            else: # means that the fabricator is in the db but not in the list
                newFab = Fabricator(serialPort, name=dbFab.getName())
                self.fabricators.append(newFab)
        else: # means that the fabricator is not in the db
            if listFab is not None: # means that the fabricator is in the list but not in the db
                newFab = listFab
                db.session.add(newFab)
                db.session.commit()
            else: # means that the fabricator is not in the list or the db
                newFab = Fabricator(serialPort, name=name)
                self.fabricators.append(newFab)
                db.session.add(newFab)
                db.session.commit()
        dbFabricators = Fabricator.queryAll()
        assert(len(self) == len(dbFabricators)), f"len(self)={len(self)}, len(dbFabricators)={len(dbFabricators)}"
        # TODO: figure out how to check if the fabricator is in the db
        # assert all(fabricator in self.fabricators for fabricator in dbFabricators), f"self={self.fabricators}, dbFabricators={dbFabricators}"

        # NEW: No thread creation - idle monitor automatically monitors this fabricator
        if newFab:
            print(f"[FabricatorList] Added fabricator: {newFab.name} (will be monitored by idle thread)")

    def deleteFabricator(self, fabricator_id):
        """
        delete a fabricator from the list, and from the database
        :param int fabricator_id: the id of the fabricator to delete
        :return: True if the fabricator was deleted, False otherwise
        :rtype: bool
        """
        fabricator = self.getFabricatorById(fabricator_id)
        if fabricator:
            try:
                self.fabricators.remove(fabricator)
                Fabricator.query.filter_by(dbID=fabricator_id).delete()
                db.session.commit()
            except Exception as e:
                return app.handle_errors_and_logging(e)
            return True

    def getFabricatorByName(self, name) -> Fabricator | None:
        """
        find the first fabricator with the given name
        :param str name: the name to search for
        :return: the first fabricator with the given name, or None if no fabricator has that name
        :rtype: Fabricator | None
        """
        return next((fabricator for fabricator in self if fabricator.getName() == name), None)


    def getFabricatorByHwid(self, hwid) -> Fabricator | None:
        """
        find the first fabricator with the given hwid
        :param str hwid: the hwid to search for
        :return: the first fabricator with the given hwid, or None if no fabricator has that hwid
        :rtype: Fabricator | None
        """
        return next((fabricator for fabricator in self if fabricator.getHwid() == hwid), None)

    def getFabricatorById(self, dbID) -> Fabricator | None:
        """
        find the first fabricator with the given id
        :param int dbID: the id to search for
        :return: the first fabricator with the given id, or None if no fabricator has that id
        :rtype: Fabricator | None
        """
        return next((fabricator for fabricator in self if fabricator.dbID == dbID), None)

    def getFabricatorByPort(self, port) -> Fabricator | None:
        """
        find the first fabricator with the given port
        :param str | ListPortInfo | SysFS port: the port to search for
        :return: the first fabricator with the given port, or None if no fabricator has that port
        :rtype: Fabricator | None
        """
        if isinstance(port, (ListPortInfo, SysFS)): port = port.device
        assert isinstance(port, str), f"port={port}, type(port)={type(port)}"
        for fabricator in self:
            assert isinstance(fabricator.devicePort, str), f"fabricator.devicePort={fabricator.devicePort}, type(fabricator.devicePort)={type(fabricator.devicePort)}"
            if fabricator.devicePort == port:
                return fabricator
        return next((fabricator for fabricator in self.fabricators if fabricator.devicePort == port), None)

    def start_print_job(self, fabricator: Fabricator, job: Job):
        """
        Start a print job by spawning a dedicated PrintWorkerThread.

        NEW METHOD (replaces old per-fabricator thread model)

        :param fabricator: Fabricator to execute the print
        :param job: Job to print
        """
        # Check if there's already a print thread for this fabricator
        if fabricator.dbID in self.active_print_threads:
            print(f"[FabricatorList] WARNING: Fabricator {fabricator.name} already has an active print thread")
            return

        # Create and start print worker thread
        print_thread = PrintWorkerThread(fabricator, job, self, self.app)
        self.active_print_threads[fabricator.dbID] = print_thread
        print_thread.start()

        print(f"[FabricatorList] Started print thread for {fabricator.name}, Job {job.id}")

    def print_completed(self, fabricator: Fabricator, success: bool):
        """
        Callback invoked when a print job completes or fails.
        Cleans up the print worker thread.

        NEW METHOD

        :param fabricator: Fabricator that completed the print
        :param success: True if print succeeded, False if failed/cancelled
        """
        # Remove print thread from active list
        if fabricator.dbID in self.active_print_threads:
            del self.active_print_threads[fabricator.dbID]
            print(f"[FabricatorList] Print completed for {fabricator.name}, success={success}")

        # Fabricator is now idle again - idle monitor will pick it up
        # No need to explicitly notify - idle monitor checks periodically

    def restore_queues_from_database(self):
        """
        Load all jobs with status='inqueue' from database and populate fabricator queues.
        Called during initialization to restore queue state after server restart.

        NEW METHOD
        """
        try:
            # Query all jobs that should be in queues
            pending_jobs = Job.query.filter_by(status='inqueue').order_by(Job.queue_position).all()

            if not pending_jobs:
                print("[FabricatorList] No pending jobs to restore")
                return

            # Group jobs by fabricator
            from collections import defaultdict
            jobs_by_fabricator = defaultdict(list)
            for job in pending_jobs:
                if job.fabricator_id:
                    jobs_by_fabricator[job.fabricator_id].append(job)

            # Add jobs to appropriate fabricator queues
            restored_count = 0
            for fabricator in self.fabricators:
                if fabricator.dbID in jobs_by_fabricator:
                    jobs = jobs_by_fabricator[fabricator.dbID]
                    for job in jobs:
                        fabricator.queue.addToBack(job)
                        restored_count += 1

            print(f"[FabricatorList] Restored {restored_count} jobs to {len(jobs_by_fabricator)} fabricator queues")

        except Exception as e:
            print(f"[FabricatorList] Error restoring queues: {e}")
            self.app.handle_errors_and_logging(e)

    def queue_restore(self, status: str, queue: Queue):
        """
        Restore the queue for the given fabricator
        :param str status: the status of the fabricator
        :param Queue queue: the queue to restore
        """
        for fabricator in self.fabricators:
            for job in queue:
                if job.status != 'inqueue':
                    job.setStatus('inqueue')
                    job.setDBstatus(job.id, 'inqueue')
            fabricator.setQueue(queue)
            fabricator.setStatus(status)
            self.fabricator_threads.append(self.start_fabricator_thread(fabricator))

    def update_thread(self, fabricator: Fabricator):
        """
        Update the thread for the given fabricator
        :param Fabricator fabricator:
        :return:
        """
        # thread = next(thread for thread in self.fabricator_threads if thread.fabricator.id == fabricator.id)
        while True:
            time.sleep(2)
            status = fabricator.getStatus()
            queueSize = len(fabricator.queue)
            fabricator.responseCount = 0
            if status == "ready" and queueSize > 0:
                time.sleep(2)
                if status != "offline":
                    fabricator.printNextInQueue()

    def resetThread(self, fabricator_id: int) -> tuple[Response, int]:
        """
        Reset the thread for the given fabricator
        :param int fabricator_id: the dbID of the fabricator to reset
        :return: a json response for the client
        :rtype: tuple[Response, int]
        """
        try:
            for thread in self.fabricator_threads:
                if thread.fabricator.dbID == fabricator_id:
                    fabricator = thread.fabricator
                    thread.stop()
                    self.fabricator_threads.remove(thread)
                    self.fabricator_threads.append(self.start_fabricator_thread(fabricator))
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"}), 200
        except Exception as e:
            app.handle_errors_and_logging(e)
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    def queueRestore(self, fabricator_id: int, status: str) -> tuple[Response, int]:
        """
        Restore the queue for the given fabricator
        :param int fabricator_id:
        :param str status:
        :return: a json response for the client
        :rtype: tuple[Response, int]
        """
        try:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == fabricator_id:
                    fabricator = thread.fabricator
                    thread.stop()
                    self.fabricator_threads.remove(thread)
                    self.queue_restore(status, fabricator.queue)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"}), 200
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500


    def deleteThread(self, fabricator_id: int) -> tuple[Response, int]:
        """
        Delete the thread for the given fabricator
        :param int fabricator_id: the dbID of the fabricator to delete
        :return: a json response for the client
        :rtype: tuple[Response, int]
        """
        try:
            for thread in self.fabricator_threads:
                if thread.fabricator.dbID == fabricator_id:
                    fabricator = thread.fabricator
                    if fabricator.getStatus() == "ready":
                        fabricator.terminated = 1
                    self.fabricator_threads.remove(thread)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"}), 200
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500


    def getThreadArray(self):
        return self.fabricator_threads


    def pingForStatus(self):
        pass


    def moveFabricatorList(self, fabricator_ids: list[int]) -> tuple[Response, int]:
        """
        Move the fabricator list to the given order
        :param list[int] fabricator_ids:
        :return: a json response for the client
        :rtype: tuple[Response, int]
        """
        new_thread_list = []
        for id in fabricator_ids:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == id:
                    new_thread_list.append(thread)
                    break
        self.fabricator_threads = new_thread_list
        return jsonify({"success": True, "message": "Fabricator list reordered successfully"}), 200

    def editName(self, fabricator_id: int, name: str) -> tuple[Response, int]:
        """
        Edit the name of a registered fabricator.
        :param int fabricator_id: the dbID of the fabricator to edit
        :param str name: the new name for the fabricator
        :return: a json response for the client
        :rtype: tuple[Response, int]
        """
        fabricator = self.getFabricatorById(fabricator_id)
        if fabricator:
            fabricator.setName(name)
            return jsonify({"success": True, "message": "Fabricator name updated successfully"}), 200
        else:
            return jsonify({"error": "Fabricator not found"}), 404
# NOTE: Old FabricatorThread class has been REMOVED
# Replaced by:
# - IdleMonitorThread: Shared thread for monitoring all idle printers
# - PrintWorkerThread: Dedicated thread spawned per active print job
# See Classes/FabricatorThreading.py for new implementation