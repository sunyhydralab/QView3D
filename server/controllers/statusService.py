from flask import Blueprint, jsonify
from app import printer_status_service  # import the instance from app.py
from flask import Blueprint, jsonify, request
from models.jobs import Job
from models.printers import Printer

status_bp = Blueprint("status", __name__)

@status_bp.route('/ping', methods=["GET"])
def getStatus(Printer):
    pass

@status_bp.route('/getopenthreads')
def getOpenThreads():
    pass 

# this is the route that will be called by the UI to get the printers that have threads information
@status_bp.route('/getprinterinfo', methods=["GET"])
def getPrinterInfo():
    try:
        # no need to assign to a variable, just return the result
        return jsonify(printer_status_service.retrieve_printer_info())  # call the method on the instance
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@status_bp.route('/hardreset', methods=["POST"])
def hardreset():
    try: 
        data = request.get_json() # get json data 
        id = data['printerid']
        # no need to assign to a variable, just return the result
        return printer_status_service.resetThread(id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route('/queuerestore', methods=["POST"])
def queueRestore():
    try: 
        data = request.get_json() # get json data 
        id = data['printerid']
        status = data['status']
        # no need to assign to a variable, just return the result
        return printer_status_service.queueRestore(id, status)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        # no need to assign to a variable, just return the result
        return printer_status_service.deleteThread(printerid)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/editNameInThread", methods=["POST"])
def editName(): 
    try: 
        data = request.get_json() 
        printerid = data['printerid']
        name = data['newname']
        # no need to assign to a variable, just return the result
        return printer_status_service.editName(printerid, name)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
