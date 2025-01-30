from flask import jsonify, Response
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy import inspect
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Jobs import Job
from Classes.Queue import Queue
from threading import Thread
import time
from globals import current_app as app, tabs
from models.db import db

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
        """stop all fabricator threads"""
        [thread.stop() for thread in self.fabricator_threads]
        self.fabricator_threads = []

    def addFabricator(self, serialPortName: str, name: str = ""):
        """
        add a fabricator to the list, and to the database, then start a thread for it
        :param str serialPortName: the name of the serial port to add
        :param str name: the name of the fabricator to add
        """
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in self if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        newFab: Fabricator | None = None
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                app.handle_errors_and_logging(Exception(f"Fabricator {dbFab.getName()} already exists in the list"), listFab)
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
    def __init__(self, fabricator: Fabricator, passed_app=app, *args, **kwargs):
        """
        create a new FabricatorThread for the given fabricator
        :param Fabricator fabricator: the fabricator to create a thread for
        :param MyFlaskApp passed_app: the app for context actions
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
        with self.app.app_context():
            self.fabricator.responseCount = 0
            while True:
                time.sleep(2)
                queueSize = len(self.fabricator.queue)
                if self.fabricator.getStatus() == "printing" and queueSize > 0:
                    assert isinstance(self.fabricator.queue[0], Job), f"self.fabricator.queue[0]={self.fabricator.queue[0]}, type(self.fabricator.queue[0])={type(self.fabricator.queue[0])}, self.fabricator.queue={self.fabricator.queue}, type(self.fabricator.queue)={type(self.fabricator.queue)}"
                    if self.fabricator.queue[0].released == 1:
                        if not self.fabricator.begin():
                            self.app.handle_errors_and_logging(Exception(f"Fabricator {self.fabricator.getName()} failed to begin") if not self.fabricator.error else self.fabricator.error, level=50)

    def stop(self):
        self.fabricator.terminated = 1
