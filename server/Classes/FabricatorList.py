from flask import jsonify
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from sqlalchemy import inspect
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Jobs import Job
from Classes.Queue import Queue
from threading import Thread
import time
from globals import current_app as app
from models.db import db

class FabricatorList:
    def __init__(self, app=None):
        self.app = app
        assert self.app is not None, "app is None"
        with self.app.app_context():
            if not inspect(db.engine).has_table('fabricator') or not Fabricator.metadata.tables:
                Fabricator.metadata.create_all(db.engine)
            self.fabricators = Fabricator.queryAll()
            self.fabricator_threads = []
            self.ping_thread = None
            for fabricator in self.fabricators:
                fabricator.device.connect()
                self.fabricator_threads.append(self.start_fabricator_thread(fabricator))

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
                newFab.addToDB()
            else: # means that the fabricator is not in the list or the db
                newFab = Fabricator(serialPort, name=name)
                self.fabricators.append(newFab)
        dbFabricators = Fabricator.queryAll()
        assert(len(self) == len(dbFabricators)), f"len(self)={len(self)}, len(dbFabricators)={len(dbFabricators)}"
        # TODO: figure out how to check if the fabricator is in the db
        # assert all(fabricator in self.fabricators for fabricator in dbFabricators), f"self={self.fabricators}, dbFabricators={dbFabricators}"
        if newFab:
            print("starting new fabricator thread")
            self.start_fabricator_thread(newFab)

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
                Fabricator.query.filter_by(dbID=fabricatorid).delete()
                Fabricator.updateDB()
            except ValueError as e:
                app.handle_errors_and_logging(e)
                return e
            except Exception as e:
                app.handle_errors_and_logging(e)
                return False
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


    # def diagnose(self, device: Device | Fabricator):
    #     """diagnose a fabricator"""
    #     if isinstance(device, Fabricator):
    #         device = device.device
    #     try:
    #         diagnoseString = ""
    #         for port in serial.tools.list_ports.comports():
    #             if port.device == device.getSerialPort().device:
    #                 diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
    #                 hwid = device.getHWID()
    #                 fabricatorExists = self.getFabricatorByHwid(hwid)
    #                 if fabricatorExists:
    #                     fabricator = self.getFabricatorByHwid(hwid)
    #                     diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {fabricator.name} <br> <b>Device:</b> {fabricator.device}, <br> <b>Description:</b> {fabricator.description}, <br><b> HWID:</b> {fabricator.hwid}"
    #         if diagnoseString == "":
    #             diagnoseString = "The port this fabricator is registered under is <b>not found</b>. Please check the connection and try again."
    #         return {
    #             "success": True,
    #             "message": "fabricator successfully diagnosed.",
    #             "diagnoseString": diagnoseString,
    #         }
    #
    #     except Exception as e:
    #         print(f"Unexpected error: {e}")
    #         return jsonify({"error": "Unexpected error occurred"}), 500


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
        thread = next(thread for thread in self.fabricator_threads if thread.fabricator == fabricator)
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
            fabricator_thread = self.start_fabricator_thread(fabricator)
            self.fabricator_threads.append(fabricator_thread)

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
            queueSize = len(fabricator)
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
                    fabricator.terminated = 1
                    thread_data = {
                        "id": fabricator.dbID,
                        "device": fabricator.device,
                        "description": fabricator.description,
                        "hwid": fabricator.hwid,
                        "name": fabricator.name,
                    }
                    self.fabricator_threads.remove(thread)
                    self.fabricator_threads.append(self.start_fabricator_thread(fabricator))
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
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
                    fabricator.terminated = 1
                    thread_data = {
                        "id": fabricator.id,
                        "device": fabricator.device,
                        "description": fabricator.description,
                        "hwid": fabricator.hwid,
                        "name": fabricator.name,
                    }
                    self.fabricator_threads.remove(thread)
                    self.queue_restore(status, fabricator.queue)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
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
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
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
        return jsonify({"success": True, "message": "Fabricator list reordered successfully"})

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
            return jsonify({"success": True, "message": "Fabricator name updated successfully"})
        else:
            return jsonify({"error": "Fabricator not found"}), 404

class FabricatorThread(Thread):
    def __init__(self, fabricator, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fabricator: Fabricator = fabricator
        if app:
            self.app = app
        else:
            from globals import current_app
            self.app = current_app

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
            while True:
                time.sleep(2)
                status = self.fabricator.getStatus()
                queueSize = len(self.fabricator.queue)
                self.fabricator.responseCount = 0
                if status == "printing":
                    if queueSize > 0:
                        assert isinstance(self.fabricator.queue[0],
                                          Job), f"self.fabricator.queue[0]={self.fabricator.queue[0]}, type(self.fabricator.queue[0])={type(self.fabricator.queue[0])}, self.fabricator.queue={self.fabricator.queue}, type(self.fabricator.queue)={type(self.fabricator.queue)}"
                if status == "printing" and queueSize > 0 and self.fabricator.queue[0].released == 1:
                    time.sleep(2)
                    if status != "offline":
                        self.fabricator.begin()

    def stop(self):
        self.fabricator.terminated = 1
