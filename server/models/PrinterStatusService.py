from threading import Thread
from models.printers import Printer
import serial
import serial.tools.list_ports
import time
import requests
from Classes.Queue import Queue
from flask import jsonify 

class PrinterThread(Thread):
    def __init__(self, printer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.printer = printer

class PrinterStatusService:
    # in order to access the app context, we need to pass the app to the PrinterStatusService, mainly for the websockets
    def __init__(self, app):
        self.ping_thread = None
        self.app = app
        self.socketio = socketio
        self.printer_threads = []  # array of printer threads

    def start_printer_thread(self, printer):
        # also pass the app to the printer thread
        thread = PrinterThread(printer, target=self.update_thread, args=(printer, self.app)) 
        thread.daemon = True #lets you kill the thread when the main program exits, allows for the server to be shut down
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        # all printer statuses initialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset printer' command.
        for printer_info in printers_data:
            printer = Printer(
                id=printer_info["id"],
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
                status='configuring',
            )
            printer_thread = self.start_printer_thread(
                printer
            )  # creating a thread for each printer object
            self.printer_threads.append(printer_thread)

        # creating separate thread to loop through all of the printer threads to ping them for print status
        self.ping_thread = Thread(target=self.pingForStatus)

    
    def queue_restore(self, printers_data, status, queue):
        # all printer statuses initialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset printer' command.
        for printer_info in printers_data:
            printer = Printer(
                id=printer_info["id"],
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
            )
            for job in queue: 
                if(job.status!='inqueue'):
                    job.setStatus('inqueue')
                    job.setDBstatus(job.id, 'inqueue')
            printer.setQueue(queue)
            printer.setStatus(status)
            printer_thread = self.start_printer_thread(
                printer
            )  # creating a thread for each printer object
            self.printer_threads.append(printer_thread)

    # passing app here to access the app context
    def update_thread(self, printer, app):
        with app.app_context():
            while True:
                time.sleep(2)
                status = printer.getStatus()  # get printer status

                queueSize = printer.getQueue().getSize() # get size of queue 
                printer.responseCount = 0 
                if (status == "ready" and queueSize > 0):
                    time.sleep(2) # wait for 2 seconds to allow the printer to process the queue
                    if status != "offline": 
                        printer.printNextInQueue()

    def resetThread(self, printer_id):
        try: 
            for thread in self.printer_threads:
                if thread.printer.id == printer_id:    
                    printer = thread.printer
                    printer.terminated = 1 
                    thread_data = {
                        "id": printer.id, 
                        "device": printer.device,
                        "description": printer.description,
                        "hwid": printer.hwid,
                        "name": printer.name, 
                    }
                    self.printer_threads.remove(thread)
                    self.create_printer_threads([thread_data])
                    break
            return jsonify({"success": True, "message": "Printer thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500
        
    
    def queueRestore(self, printer_id, status):
        try: 
            for thread in self.printer_threads:
                if thread.printer.id == printer_id:    
                    printer = thread.printer
                    printer.terminated = 1 
                    thread_data = {
                        "id": printer.id, 
                        "device": printer.device,
                        "description": printer.description,
                        "hwid": printer.hwid,
                        "name": printer.name, 
                    }
                    self.printer_threads.remove(thread)
                    self.queue_restore([thread_data], status, printer.getQueue())
                    break
            return jsonify({"success": True, "message": "Printer thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500
        
    def deleteThread(self, printer_id):
        try: 
            for thread in self.printer_threads:
                if thread.printer.id == printer_id:    
                    printer = thread.printer
                    thread_data = {
                        "id": printer.id, 
                        "device": printer.device,
                        "description": printer.description,
                        "hwid": printer.hwid,
                        "name": printer.name
                    }
                    self.printer_threads.remove(thread)
                    break
            return jsonify({"success": True, "message": "Printer thread reset successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500
        
    def editName(self, printer_id, name):
        try: 
            for thread in self.printer_threads:
                if thread.printer.id == printer_id:    
                    printer = thread.printer
                    printer.name = name
                    break
            return jsonify({"success": True, "message": "Printer name updated successfully"})
        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"success": False, "error": "Unexpected error occurred"}), 500
        

    # this method will be called by the UI to get the printers that have a threads information
    def retrieve_printer_info(self):
        printer_info_list = []
        for thread in self.printer_threads:
            printer = (
                thread.printer
            )  # get the printer object associated with the thread
            printer_info = {
                "device": printer.device,
                "description": printer.description,
                "hwid": printer.hwid,
                "name": printer.name,
                "status": printer.status,
                "id": printer.id,
                "error": printer.error, 
                "canPause": printer.canPause,
                "queue": [], # empty queue to store job objects 
                "colorChangeBuffer": printer.colorbuff
                # "colorChangeBuffer": printer.colorChangeBuffer
            }
            queue = printer.getQueue()
            for job in queue: 
                job_info = {
                    "id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "date": job.date.strftime('%a, %d %b %Y %H:%M:%S'),
                    "printerid": job.printer_id, 
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
                    "printer_name": job.printer_name,
                    "max_layer_height": job.max_layer_height,
                    "current_layer_height": job.current_layer_height,
                    "filament": job.filament,
                }
                printer_info['queue'].append(job_info)
            
            printer_info_list.append(printer_info)
            
        return printer_info_list

    def getThreadArray(self):
        return self.printer_threads
    
    def pingForStatus(self):
        """_summary_ pseudo code
        for printer in threads:
            status = printer.getStatus()
            if status == printing:
                GCODE for print status
        """
        pass
    
    def movePrinterList(self, printer_ids):
        # printer_ids is a list of printer ids in the order they should be displayed
        new_thread_list = []
        for id in printer_ids:
            for thread in self.printer_threads:
                if thread.printer.id == id:
                    new_thread_list.append(thread)
                    break
        self.printer_threads = new_thread_list
        return jsonify({"success": True, "message": "Printer list reordered successfully"})
    
    def add_printer(self, printer_data):
        printer = Printer(**printer_data)
        # add the printer to the list of printer threads
        print("Adding printer:", printer)
        self.printer_threads.append(PrinterThread(printer, target=self.update_thread, args=(printer, self.app)))

