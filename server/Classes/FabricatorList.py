from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy import inspect

from Classes.Fabricators.Printers.Printer import Printer
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Jobs import Job
from Classes.Queue import Queue
from threading import Thread
import time
from services.app_service import current_app as app
from utils.formatting import tabs
from config.db import db

class FabricatorList:
    def __init__(self, passed_app=app):
        print(f"{tabs(tab_change=1)}setting app...", end="")
        self.app = passed_app
        print(" Done")
        with self.app.app_context():
            print(f"{tabs()}initializing fabricator table...", end="")
            if not inspect(db.engine).has_table('Fabricators') or not Fabricator.metadata.tables:
                Fabricator.metadata.create_all(db.engine)
            print(" Done")
            print(f"{tabs()}querying fabricators...", end="")
            self.fabricators = Fabricator.queryAll()
            print(f" Done: {len(self.fabricators)} fabricator{"s" if len(self.fabricators) != 1 else ""} found")
            print(f"{tabs()}initializing fabricator threads...")
            self.fabricator_threads = []
            self.ping_thread = None
            self.health_monitor_thread = None
            for fabricator in self.fabricators:
                print(f"{tabs(tab_change=1)}initializing fabricator for {fabricator.getName()}...")
                print(f"{tabs(tab_change=1)}connecting to {fabricator.devicePort}...")
                fabricator.device.connect()
                print(f"{tabs()}connected to {fabricator.devicePort}")
                print(f"{tabs()}initializing thread for {fabricator.getName()}...", end="")
                self.fabricator_threads.append(self.start_fabricator_thread(fabricator))
                print(" Done")
                print(f"{tabs(tab_change=-1)}fabricator for {fabricator.getName()} initialized")
            print(f"{tabs(tab_change=-1)}fabricator threads initialized")

            # Start health monitoring
            print(f"{tabs()}starting thread health monitor...", end="")
            self.health_monitor_thread = HealthMonitorThread(self, self.app)
            self.health_monitor_thread.start()
            print(" Done")

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
        """Stop all fabricator threads and health monitor"""
        if self.health_monitor_thread:
            self.health_monitor_thread.stop()
        [thread.stop() for thread in self.fabricator_threads]
        self.fabricator_threads = []

    def addFabricator(self, serialPortName: str, name: str = ""):
        """
        add a fabricator to the list, and to the database, then start a thread for it
        :param str serialPortName: the name of the serial port to add
        :param str name: the name of the fabricator to add
        """
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        if serialPort is None:
            err = Exception(f"Serial port '{serialPortName}' not found. Please make sure the device is connected.")
            app.handle_errors_and_logging(err)
            raise err
        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in self if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        newFab: Fabricator | None = None
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                err = Exception(f"This fabricator is already registered as {dbFab.getName()}")
                app.handle_errors_and_logging(err, listFab.device.logger)
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
        dbFabricators = Fabricator.queryAll()
        assert(len(self) == len(dbFabricators)), f"len(self)={len(self)}, len(dbFabricators)={len(dbFabricators)}"
        # TODO: figure out how to check if the fabricator is in the db
        # assert all(fabricator in self.fabricators for fabricator in dbFabricators), f"self={self.fabricators}, dbFabricators={dbFabricators}"
        if newFab:
            self.fabricator_threads.append(self.start_fabricator_thread(newFab))

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
        if isinstance(port, ListPortInfo or SysFS): port = port.device
        assert isinstance(port, str), f"port={port}, type(port)={type(port)}"
        for fabricator in self:
            assert isinstance(fabricator.devicePort, str), f"fabricator.devicePort={fabricator.devicePort}, type(fabricator.devicePort)={type(fabricator.devicePort)}"
            if fabricator.devicePort == port:
                return fabricator
        return next((fabricator for fabricator in self.fabricators if fabricator.devicePort == port), None)

    def start_fabricator_thread(self, fabricator: Fabricator):
        """
        Start a thread for the given fabricator
        :param Fabricator fabricator: the given fabricator
        :return:
        :rtype: FabricatorThread
        """
        thread = FabricatorThread(fabricator, passed_app=self.app, **{"daemon": True})
        thread.start()
        return thread


    def create_fabricator_threads(self):
        """Create a thread for each fabricator in the list and start it"""
        for fabricator in self:
            fabricator.queue = Queue()  # Ensure each fabricator has its own queue
            fabricator_thread = self.start_fabricator_thread(fabricator)
            self.fabricator_threads.append(fabricator_thread)
        self.ping_thread = Thread(target=self.pingForStatus)

    def get_fabricator_thread(self, fabricator):
        """
        Get the thread for the given fabricator
        :param fabricator: the given fabricator
        :return: that fabricator's thread
        """
        assert fabricator in self, f"fabricator {fabricator} not in self"
        thread = next((thread for thread in self.fabricator_threads if thread.fabricator == fabricator), None)
        if thread is None:
            raise ValueError(f"Fabricator {fabricator} has no thread")
        assert isinstance(thread, FabricatorThread), f"thread={thread}, type(thread)={type(thread)}"
        assert thread.is_alive(), f"thread {thread} is not alive"
        assert thread.daemon, f"thread {thread} is not daemon"
        return thread

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

class FabricatorThread(Thread):
    terminated = False
    def __init__(self, fabricator: Fabricator, passed_app=app, *args, **kwargs):
        """
        create a new FabricatorThread for the given fabricator
        :param Fabricator fabricator: the fabricator to create a thread for
        :param QViewApp passed_app: the app for context actions
        """
        super().__init__(*args, **kwargs)
        self.fabricator: Fabricator = fabricator
        self.app = passed_app
        self.daemon = kwargs.get('daemon', False)

    def __repr__(self):
        return f"FabricatorThread(fabricator={self.fabricator}, daemon={self.daemon}, running={self.is_alive()})"

    def __to_JSON__(self):
        """
        Convert the FabricatorThread to a JSON object that can be sent to the frontend
        :rtype: dict
        """
        return {
            "fabricator": self.fabricator,
            "app": self.app,
            "running": self.is_alive(),
            "daemon": self.daemon,
        }

    def run(self):
        """Main thread loop - monitors fabricator status and processes job queue"""
        with self.app.app_context():
            from config.config import Config

            self.fabricator.responseCount = 0

            # Load queue configuration
            autoProgress = Config.get('queue_auto_progress', True)
            progressDelay = Config.get('queue_auto_progress_delay', 2)

            while not self.terminated:
                time.sleep(.5)

                status = self.fabricator.getStatus()
                queue = self.fabricator.queue
                queueSize = len(queue)

                # Auto-progress when job finishes
                if autoProgress and status in ["complete", "cancelled", "misprint", "error"]:
                    self._handleJobCompletion(queue, queueSize, progressDelay)

                # Start next job if ready
                elif status == "ready" and queueSize > 0:
                    self._processNextJob(queue, autoProgress)

                # Wait for homing to complete
                elif self.fabricator.device.status == "homing":
                    while self.fabricator.device.status == "homing":
                        time.sleep(.5)

                # Monitor temperature when idle
                elif isinstance(self.fabricator.device, Printer) and status == "ready":
                    self.fabricator.device.handleTempLine(self.fabricator.device.serialConnection.read())

    def _handleJobCompletion(self, queue, queueSize, delay):
        """Handle completion of current job and transition to next"""
        if queueSize == 0:
            self.fabricator.setStatus("idle")
            return

        completedJob = queue[0]

        # Log completion before removal
        if self.app.logger:
            remaining_after_removal = queueSize - 1
            if remaining_after_removal > 0:
                self.app.logger.info(
                    f"Fabricator {self.fabricator.getName()} completed job {completedJob.id}. "
                    f"{remaining_after_removal} job(s) remaining. Auto-progressing in {delay}s..."
                )
            else:
                self.app.logger.info(
                    f"Fabricator {self.fabricator.getName()} completed job {completedJob.id}. "
                    f"Queue empty, going idle."
                )

        # Sleep before transitioning to prevent immediate re-processing
        time.sleep(delay)

        # Remove completed job and check remaining queue
        queue.removeJob(fabricator_id=self.fabricator.dbID)
        remaining = len(queue)

        if remaining > 0:
            # More jobs waiting - transition to ready to trigger next job
            self.fabricator.setStatus("ready")
        else:
            # Queue empty - go idle
            self.fabricator.setStatus("idle")

    def _processNextJob(self, queue, autoProgress):
        """Process the next job in the queue"""
        assert isinstance(queue[0], Job), (
            f"Expected Job instance, got {type(queue[0])}"
        )

        # Auto-release if enabled
        if autoProgress and queue[0].released == 0:
            queue[0].setReleased(1)
            if self.app.logger:
                self.app.logger.info(
                    f"Auto-releasing job {queue[0].id} for {self.fabricator.getName()}"
                )

        # Begin printing if released
        if queue[0].released == 1:
            self.fabricator.setStatus("printing")
            if not self.fabricator.begin():
                error = (
                    self.fabricator.error or
                    Exception(f"Fabricator {self.fabricator.getName()} failed to begin")
                )
                self.app.handle_errors_and_logging(error, level=50)

    def stop(self):
        self.terminated = True


class HealthMonitorThread(Thread):
    """Monitors fabricator threads and restarts dead ones"""
    terminated = False

    def __init__(self, fabricator_list, passed_app=app, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fabricator_list = fabricator_list
        self.app = passed_app
        self.daemon = True
        from config.config import Config
        self.check_interval = Config.get('thread_health_check_interval', 30)

    def run(self):
        """Check thread health every interval"""
        with self.app.app_context():
            while not self.terminated:
                time.sleep(self.check_interval)

                for thread in list(self.fabricator_list.fabricator_threads):
                    if not thread.is_alive() and not thread.terminated:
                        # Thread died unexpectedly
                        fabricator = thread.fabricator
                        if self.app.logger:
                            self.app.logger.error(
                                f"Thread for {fabricator.getName()} died unexpectedly, restarting"
                            )

                        # Remove dead thread
                        self.fabricator_list.fabricator_threads.remove(thread)

                        # Start new thread
                        new_thread = self.fabricator_list.start_fabricator_thread(fabricator)
                        self.fabricator_list.fabricator_threads.append(new_thread)

    def stop(self):
        self.terminated = True
