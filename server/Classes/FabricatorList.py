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
    def __init__(self, fabricator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fabricator = fabricator

class FabricatorList():
    fabricators: [Fabricator] = []
    fabricator_threads = []
    ping_thread = None

    @staticmethod
    def __iter__():
        return iter(FabricatorList.fabricators)

    @staticmethod
    def __len__():
        return len(FabricatorList.fabricators)

    @staticmethod
    def init():
        """initialize the list of printers"""
        FabricatorList.fabricators = Fabricator.queryAll()

    @staticmethod
    def addFabricator(serialPortName: str, name: str = ""):
        """add a printer to the list, and to the database"""
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.hwid == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                print("Fabricator is already in the list and the db")
            else: # means that the fabricator is in the db but not in the list
                FabricatorList.fabricators.append(Fabricator(serialPort, name=dbFab.getname()))
        else: # means that the fabricator is not in the db
            if listFab is not None: # means that the fabricator is in the list but not in the db
                listFab.addToDB()
            else: # means that the fabricator is not in the list or the db
                FabricatorList.fabricators.append(Fabricator(serialPort, name=name, addToDB=True))
        dbPrinters = Fabricator.queryAll()
        assert(len(FabricatorList.fabricators) == len(dbPrinters))
        assert all(printer in FabricatorList.fabricators for printer in dbPrinters)

    @staticmethod
    def deleteFabricator(printerid):
        """delete a printer from the list, and from the database"""
        # TODO: Implement deleteFabricator
        pass

    @staticmethod
    def getFabricatorByName(name) -> Fabricator | None:
        """find the first printer with the given name"""
        return next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getName() == name), None)

    @staticmethod
    def getPrinterByHwid(hwid) -> Fabricator | None:
        """find the first printer with the given hwid"""
        return next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getHwid() == hwid), None)

    @staticmethod
    def diagnose(device: Device):
        try:
            diagnoseString = ""
            for port in serial.tools.list_ports.comports():
                if port.device == device.getSerialPort().device:
                    diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
                    hwid = device.getHWID()
                    printerExists = FabricatorList.getPrinterByHwid(hwid)
                    if printerExists:
                        printer = FabricatorList.getPrinterByHwid(hwid)
                        diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {printer.name} <br> <b>Device:</b> {printer.device}, <br> <b>Description:</b> {printer.description}, <br><b> HWID:</b> {printer.hwid}"
            if diagnoseString == "":
                diagnoseString = "The port this printer is registered under is <b>not found</b>. Please check the connection and try again."
            return {
                "success": True,
                "message": "Printer successfully diagnosed.",
                "diagnoseString": diagnoseString,
            }

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500

    @staticmethod
    def start_fabricator_thread(fabricator, app):
        thread = FabricatorThread(fabricator, target=FabricatorList.update_thread, args=(fabricator, app))
        thread.daemon = True
        thread.start()
        return thread

    @staticmethod
    def create_fabricator_threads(fabricators_data, app):
        for fabricator_info in fabricators_data:
            fabricator = Fabricator(
                id=fabricator_info["id"],
                device=fabricator_info["device"],
                description=fabricator_info["description"],
                hwid=fabricator_info["hwid"],
                name=fabricator_info["name"],
                status='configuring',
            )
            fabricator.setQueue(Queue())  # Ensure each fabricator has its own queue
            fabricator_thread = FabricatorList.start_fabricator_thread(fabricator, app)
            FabricatorList.fabricator_threads.append(fabricator_thread)

        FabricatorList.ping_thread = Thread(target=FabricatorList.pingForStatus)

    @staticmethod
    def queue_restore(fabricators_data, status, queue, app):
        for fabricator_info in fabricators_data:
            fabricator = Fabricator(
                id=fabricator_info["id"],
                device=fabricator_info["device"],
                description=fabricator_info["description"],
                hwid=fabricator_info["hwid"],
                name=fabricator_info["name"],
            )
            for job in queue:
                if job.status != 'inqueue':
                    job.setStatus('inqueue')
                    job.setDBstatus(job.id, 'inqueue')
            fabricator.setQueue(queue)
            fabricator.setStatus(status)
            fabricator_thread = FabricatorList.start_fabricator_thread(fabricator, app)
            FabricatorList.fabricator_threads.append(fabricator_thread)

    @staticmethod
    def update_thread(fabricator, app):
        with app.app_context():
            while True:
                time.sleep(2)
                status = fabricator.getStatus()
                queueSize = fabricator.getQueue().getSize()
                fabricator.responseCount = 0
                if status == "ready" and queueSize > 0:
                    time.sleep(2)
                    if status != "offline":
                        fabricator.printNextInQueue()

    @staticmethod
    def resetThread(fabricator_id, app):
        try:
            for thread in FabricatorList.fabricator_threads:
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
                    FabricatorList.fabricator_threads.remove(thread)
                    FabricatorList.create_fabricator_threads([thread_data], app)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    @staticmethod
    def queueRestore(fabricator_id, status, app):
        try:
            for thread in FabricatorList.fabricator_threads:
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
                    FabricatorList.fabricator_threads.remove(thread)
                    FabricatorList.queue_restore([thread_data], status, fabricator.getQueue(), app)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    @staticmethod
    def deleteThread(fabricator_id):
        try:
            for thread in FabricatorList.fabricator_threads:
                if thread.fabricator.id == fabricator_id:
                    fabricator = thread.fabricator
                    thread_data = {
                        "id": fabricator.id,
                        "device": fabricator.device,
                        "description": fabricator.description,
                        "hwid": fabricator.hwid,
                        "name": fabricator.name
                    }
                    FabricatorList.fabricator_threads.remove(thread)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    @staticmethod
    def editName(fabricator_id, name):
        try:
            for thread in FabricatorList.fabricator_threads:
                if thread.fabricator.id == fabricator_id:
                    fabricator = thread.fabricator
                    fabricator.name = name
                    break
            return jsonify({"success": True, "message": "Fabricator name updated successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    @staticmethod
    def retrieve_fabricator_info():
        fabricator_info_list = []
        for thread in FabricatorList.fabricator_threads:
            fabricator = thread.fabricator
            fabricator_info = {
                "device": fabricator.device,
                "description": fabricator.description,
                "hwid": fabricator.hwid,
                "name": fabricator.name,
                "status": fabricator.status,
                "id": fabricator.id,
                "error": fabricator.error,
                "canPause": fabricator.canPause,
                "queue": [],
                "colorChangeBuffer": fabricator.colorbuff
            }
            queue = fabricator.getQueue()
            for job in queue:
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "date": job.date.strftime('%a, %d %b %Y %H:%M:%S'),
                    "fabricatorid": job.fabricator_id,
                    "errorid": job.error_id,
                    "file_name_original": job.file_name_original,
                    "progress": job.progress,
                    "sent_lines": job.sent_lines,
                    "favorite": job.favorite,
                    "released": job.released,
                    "file_pause": job.filePause,
                    "comments": job.comments,
                    "extruded": job.extruded,
                    "td_id": job.td_id,
                    "time_started": job.time_started,
                    "fabricator_name": job.fabricator_name,
                    "max_layer_height": job.max_layer_height,
                    "current_layer_height": job.current_layer_height,
                    "filament": job.filament,
                }
                fabricator_info['queue'].append(job_info)

            fabricator_info_list.append(fabricator_info)

        return fabricator_info_list

    @staticmethod
    def getThreadArray():
        return FabricatorList.fabricator_threads

    @staticmethod
    def pingForStatus():
        pass

    @staticmethod
    def moveFabricatorList(fabricator_ids):
        new_thread_list = []
        for id in fabricator_ids:
            for thread in FabricatorList.fabricator_threads:
                if thread.fabricator.id == id:
                    new_thread_list.append(thread)
                    break
        FabricatorList.fabricator_threads = new_thread_list
        return jsonify({"success": True, "message": "Fabricator list reordered successfully"})