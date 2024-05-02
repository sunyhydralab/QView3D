# get connected serial ports
import serial
import serial.tools.list_ports
import time
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request, make_response
from models.printers import Printer
# from app import printer_status_service
# from models.jobs import Job
# from models.PrinterStatusService import PrinterStatusService
# from app import printer_status_service

ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports",  methods=["GET"])
def getPorts():
    printerList = Printer.getConnectedPorts()
    return jsonify(printerList)

# method to get printers already registered with the system 
@ports_bp.route("/getprinters", methods=["GET"])
def getRegisteredPrinters():  
    try: 
        res = Printer.get_registered_printers()
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@ports_bp.route("/register", methods=["POST"])
def registerPrinter(): 
    try: 
        from app import printer_status_service
        data = request.get_json() # get json data 
        # extract data 
        device = data['printer']['device']
        description = data['printer']['description']
        hwid = data['printer']['hwid']
        name = data['printer']['name']
        

        res = Printer.create_printer(device=device, description=description, hwid=hwid, name=name, status='ready')
        if(res["success"] == True):
            id = res['printer_id']
            # hwid_parts = hwid.split('-')  # Replace '-' with the actual separator
            # hwid_without_location = '-'.join(hwid_parts[:-1])
            thread_data = {
                "id": id, 
                "device": device,
                "description": description,
                "hwid": hwid,
                "name": name
            }
            
            printer_status_service.create_printer_threads([thread_data])
        
        return res
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@ports_bp.route("/deleteprinter", methods=["POST"])
def delete_printer():
    try: 
        data = request.get_json()
        printerid = data['printerid']
        # res = printer_status_service.deleteThread(printerid)
        res = Printer.deletePrinter(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@ports_bp.route("/editname", methods=["POST"])
def edit_name(): 
    try: 
        data = request.get_json() 
        printerid = data['printerid']
        name = data['name']
        res = Printer.editName(printerid, name)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@ports_bp.route("/diagnose", methods=["POST"])
def diagnose_printer():
    try:
        data = request.get_json() 
        device = data['device']
        res = Printer.diagnosePrinter(device)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
# @ports_bp.route("/repairports", methods=["POST", "GET"])
# def repair_ports(): 
#     try:
#         ports = serial.tools.list_ports.comports()    
#         print("PORTS: ", ports)
#         for port in ports: 
#             hwid = port.hwid # get hwid 
#             print("HWID: ", hwid)

#             hwid_without_location = hwid.split(' LOCATION=')[0]
#             printer = Printer.getPrinterByHwid(hwid_without_location)
#             if printer is not None: 
#                 if(printer.getDevice()!=port.device):
#                     printer.editPort(printer.getId(), port.device)
#                     printerthread = findPrinterObject(printer.getId())
#                     printerthread.setDevice(port.device)
#         return {"success": True, "message": "Printer port(s) successfully updated."}

    # except Exception as e:
    #     print(f"Unexpected error: {e}")
    #     return jsonify({"error": "Unexpected error occurred"}), 500
    
@ports_bp.route("/movehead", methods=["POST"])
def moveHead():
    try: 
        data = request.get_json()
        port = data['port']
        
        res = Printer.moveHead(port)
        if res == "none": 
            return {"success": False, "message": "Head move unsuccessful."}
        
        return {"success": True, "message": "Head move successful."}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
        
# def findPrinterObject(printer_id): 
#     threads = printer_status_service.getThreadArray()
#     return list(filter(lambda thread: thread.printer.id == printer_id, threads))[0].printer  

@ports_bp.route("/moveprinterlist", methods=["POST"])
def movePrinterList():
    try:
        from app import printer_status_service
        data = request.get_json()
        printersIds = data['printersIds']
        # change the order of the printers threads
        res = printer_status_service.movePrinterList(printersIds) 
        if res == "none": 
            return {"success": False, "message": "Printer list not updated."}
               
        return jsonify({"success": True, "message": "Printer list successfully updated."})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500