import serial.tools.list_ports
from flask import jsonify
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS

from Classes.Fabricators.Device import Device
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Queue import Queue
from threading import Thread
import time

class FabricatorThread(Thread):
    def __init__(self, fabricator, app=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fabricator = fabricator
        if app:
            self.app = app
        else:
            from app import app
            self.app = app

    def run(self):
        with self.app.app_context():
            while True:
                time.sleep(2)
                status = self.fabricator.getStatus()
                queueSize = self.fabricator.getQueue().getSize()
                self.fabricator.responseCount = 0
                if status == "ready" and queueSize > 0:
                    time.sleep(2)
                    if status != "offline":
                        self.fabricator.printNextInQueue()

    def stop(self):
        self.fabricator.terminated = 1

class FabricatorList:
    def __init__(self, app=None):
        self.app = app
        with self.app.app_context():
            self.fabricators = Fabricator.queryAll()
            self.fabricator_threads = []
            self.ping_thread = None
            for fabricator in self.fabricators:
                self.fabricator_threads.append(self.start_fabricator_thread(fabricator))

    def __iter__(self):
        return iter(self.fabricators)

    def __len__(self):
        return len(self.fabricators)

    def __getitem__(self, key):
        return self.fabricators[key]

    def teardown(self):
        """stop all fabricator threads"""
        [thread.stop() for thread in self.fabricator_threads]
        self.fabricator_threads = []

    def addFabricator(self, serialPortName: str, name: str = ""):
        """add a fabricator to the list, and to the database, then start a thread for it"""
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in self if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        newFab: Fabricator | None = None
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                from app import handle_errors_and_logging
                handle_errors_and_logging(Exception(f"Fabricator {dbFab.getname()} already exists in the list"), listFab)
            else: # means that the fabricator is in the db but not in the list
                newFab = Fabricator(serialPort, name=dbFab.getname())
                self.fabricators.append(newFab)
        else: # means that the fabricator is not in the db
            if listFab is not None: # means that the fabricator is in the list but not in the db
                newFab = listFab
                newFab.addToDB()
            else: # means that the fabricator is not in the list or the db
                newFab = Fabricator(serialPort, name=name, addToDB=True)
                self.fabricators.append(newFab)
        dbfabricators = Fabricator.queryAll()
        assert(len(self) == len(dbfabricators))
        assert all(fabricator in self for fabricator in dbfabricators)
        if newFab: self.start_fabricator_thread(newFab)


    def deleteFabricator(self, fabricatorid):
        """delete a fabricator from the list, and from the database"""
        # TODO: Implement deleteFabricator
        pass


    def getFabricatorByName(self, name) -> Fabricator | None:
        """find the first fabricator with the given name"""
        return next((fabricator for fabricator in self if fabricator.getName() == name), None)


    def getFabricatorByHwid(self, hwid) -> Fabricator | None:
        """find the first fabricator with the given hwid"""
        return next((fabricator for fabricator in self if fabricator.getHwid() == hwid), None)

    def getFabricatorById(self, id) -> Fabricator | None:
        """find the first fabricator with the given id"""
        return next((fabricator for fabricator in self if fabricator.dbID == id), None)
    

    def getFabricatorByPort(self, port) -> Fabricator | None:
        """find the first fabricator with the given port"""
        for fabricator in self:
            if fabricator.getSerialPort().device == port:
                return fabricator
        return next((fabricator for fabricator in self.fabricators if fabricator.devicePort == port), None)


    def diagnose(self, device: Device | Fabricator):
        """diagnose a fabricator"""
        if isinstance(device, Fabricator):
            device = device.device
        try:
            diagnoseString = ""
            for port in serial.tools.list_ports.comports():
                if port.device == device.getSerialPort().device:
                    diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
                    hwid = device.getHWID()
                    fabricatorExists = self.getFabricatorByHwid(hwid)
                    if fabricatorExists:
                        fabricator = self.getFabricatorByHwid(hwid)
                        diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {fabricator.name} <br> <b>Device:</b> {fabricator.device}, <br> <b>Description:</b> {fabricator.description}, <br><b> HWID:</b> {fabricator.hwid}"
            if diagnoseString == "":
                diagnoseString = "The port this fabricator is registered under is <b>not found</b>. Please check the connection and try again."
            return {
                "success": True,
                "message": "fabricator successfully diagnosed.",
                "diagnoseString": diagnoseString,
            }

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500


    def start_fabricator_thread(self, fabricator: Fabricator):
        thread = FabricatorThread(fabricator, app=self.app, target=self.update_thread, args=(fabricator,))
        thread.daemon = True
        thread.start()
        return thread


    def create_fabricator_threads(self):
        for fabricator in self:
            fabricator.setQueue(Queue())  # Ensure each fabricator has its own queue
            fabricator_thread = self.start_fabricator_thread(fabricator)
            self.fabricator_threads.append(fabricator_thread)
        self.ping_thread = Thread(target=self.pingForStatus)

    def get_fabricator_thread(self, fabricator):
        assert fabricator in self
        thread = next(thread for thread in self.fabricator_threads if thread.fabricator == fabricator)
        assert thread.is_alive()
        assert thread.daemon
        return thread



    def queue_restore(self, status, queue):
        for fabricator in self.fabricators:
            for job in queue:
                if job.status != 'inqueue':
                    job.setStatus('inqueue')
                    job.setDBstatus(job.id, 'inqueue')
            fabricator.setQueue(queue)
            fabricator.setStatus(status)
            fabricator_thread = self.start_fabricator_thread(fabricator)
            self.fabricator_threads.append(fabricator_thread)

    def update_thread(self, fabricator):
        # thread = next(thread for thread in self.fabricator_threads if thread.fabricator.id == fabricator.id)
        while True:
            time.sleep(2)
            status = fabricator.getStatus()
            queueSize = fabricator.getQueue().getSize()
            fabricator.responseCount = 0
            if status == "ready" and queueSize > 0:
                time.sleep(2)
                if status != "offline":
                    fabricator.printNextInQueue()

    def resetThread(self, fabricator_id):
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
                    self.create_fabricator_threads()
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    def queueRestore(self, fabricator_id, status):
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
                    self.queue_restore(status, fabricator.getQueue())
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500


    def deleteThread(self, fabricator_id):
        try:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == fabricator_id:
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


    def moveFabricatorList(self, fabricator_ids):
        new_thread_list = []
        for id in fabricator_ids:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == id:
                    new_thread_list.append(thread)
                    break
        self.fabricator_threads = new_thread_list
        return jsonify({"success": True, "message": "Fabricator list reordered successfully"})