from threading import Thread
import time
from flask import jsonify

from Classes.Fabricators.Fabricator import Fabricator


class FabricatorThread(Thread):
    def __init__(self, fabricator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fabricator = fabricator


class FabricatorStatusService:
    # in order to access the app context, we need to pass the app to the FabricatorStatusService, mainly for the websockets
    def __init__(self, app):
        self.ping_thread = None
        self.app = app
        self.fabricator_threads = []  # array of fabricator threads

    # TODO: make this make sense?
    def start_fabricator_thread(self, fabricator):
        # also pass the app to the fabricator thread
        thread = FabricatorThread(fabricator, target=self.update_thread, args=(fabricator, self.app))
        thread.daemon = True  # lets you kill the thread when the main program exits, allows for the server to be shut down
        thread.start()
        return thread

    #TODO: make this make sense?
    def create_fabricator_threads(self, fabricators_data):
        # all fabricator statuses initialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset fabricator' command.
        for fabricator_info in fabricators_data:
            fabricator = Fabricator(
                id=fabricator_info["id"],
                device=fabricator_info["device"],
                description=fabricator_info["description"],
                hwid=fabricator_info["hwid"],
                name=fabricator_info["name"],
                status='configuring',
            )
            fabricator_thread = self.start_fabricator_thread(
                fabricator
            )  # creating a thread for each fabricator object
            self.fabricator_threads.append(fabricator_thread)

        # creating separate thread to loop through all of the fabricator threads to ping them for print status
        self.ping_thread = Thread(target=self.pingForStatus)

    # TODO: make this make sense?
    def queue_restore(self, fabricators_data, status, queue):
        # all fabricator statuses initialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset fabricator' command.
        for fabricator_info in fabricators_data:
            fabricator = Fabricator(
                id=fabricator_info["id"],
                device=fabricator_info["device"],
                description=fabricator_info["description"],
                hwid=fabricator_info["hwid"],
                name=fabricator_info["name"],
            )
            for job in queue:
                if (job.status != 'inqueue'):
                    job.setStatus('inqueue')
                    job.setDBstatus(job.id, 'inqueue')
            fabricator.setQueue(queue)
            fabricator.setStatus(status)
            fabricator_thread = self.start_fabricator_thread(
                fabricator
            )  # creating a thread for each fabricator object
            self.fabricator_threads.append(fabricator_thread)

    # TODO: make this make sense?
    # passing app here to access the app context
    def update_thread(self, fabricator, app):
        with app.app_context():
            while True:
                time.sleep(2)
                status = fabricator.getStatus()  # get fabricator status

                queueSize = fabricator.getQueue().getSize()  # get size of queue 
                fabricator.responseCount = 0
                if (status == "ready" and queueSize > 0):
                    time.sleep(2)  # wait for 2 seconds to allow the fabricator to process the queue
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
                    self.create_fabricator_threads([thread_data])
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
                    self.queue_restore([thread_data], status, fabricator.getQueue())
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
                    thread_data = {
                        "id": fabricator.id,
                        "device": fabricator.device,
                        "description": fabricator.description,
                        "hwid": fabricator.hwid,
                        "name": fabricator.name
                    }
                    self.fabricator_threads.remove(thread)
                    break
            return jsonify({"success": True, "message": "Fabricator thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    def editName(self, fabricator_id, name):
        try:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == fabricator_id:
                    fabricator = thread.fabricator
                    fabricator.name = name
                    break
            return jsonify({"success": True, "message": "Fabricator name updated successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500

    # this method will be called by the UI to get the fabricators that have a threads information
    def retrieve_fabricator_info(self):
        fabricator_info_list = []
        for thread in self.fabricator_threads:
            fabricator = (
                thread.fabricator
            )  # get the fabricator object associated with the thread
            fabricator_info = {
                "device": fabricator.device,
                "description": fabricator.description,
                "hwid": fabricator.hwid,
                "name": fabricator.name,
                "status": fabricator.status,
                "id": fabricator.id,
                "error": fabricator.error,
                "canPause": fabricator.canPause,
                "queue": [],  # empty queue to store job objects 
                "colorChangeBuffer": fabricator.colorbuff
                # "colorChangeBuffer": fabricator.colorChangeBuffer
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

    def getThreadArray(self):
        return self.fabricator_threads

    def pingForStatus(self):
        """_summary_ pseudo code
        for fabricator in threads:
            status = fabricator.getStatus()
            if status == printing:
                GCODE for print status
        """
        pass

    def moveFabricatorList(self, fabricator_ids):
        # fabricator_ids is a list of fabricator ids in the order they should be displayed
        new_thread_list = []
        for id in fabricator_ids:
            for thread in self.fabricator_threads:
                if thread.fabricator.id == id:
                    new_thread_list.append(thread)
                    break
        self.fabricator_threads = new_thread_list
        return jsonify({"success": True, "message": "Fabricator list reordered successfully"})

