from flask import Blueprint, jsonify, request
import os
from app import fabricator_list
status_bp = Blueprint("status", __name__)

@status_bp.route('/ping', methods=["GET"])
def getStatus():
    try:
        return jsonify({"status": "pong"}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@status_bp.route('/getopenthreads', methods=["GET"])
def getOpenThreads():
    try:
        open_threads = fabricator_list.getOpenThreads()
        return jsonify(open_threads), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# this is the route that will be called by the UI to get the printers that have threads information
@status_bp.route('/getprinterinfo', methods=["GET"])
def getPrinterInfo():
    try: 
        printer_info = fabricator_list.fabricators  # call the method on the instance
        return jsonify(printer_info)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@status_bp.route('/hardreset', methods=["POST"])
def hardreset():
    try: 
        data = request.get_json() # get json data 
        id = data['printerid']
        res = fabricator_list.resetThread(id)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route('/queuerestore', methods=["POST"])
def queueRestore():
    try: 
        data = request.get_json() # get json data 
        id = data['printerid']
        status = data['status']
        res = fabricator_list.queueRestore(id, status)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        res = fabricator_list.deleteThread(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/editNameInThread", methods=["POST"])
def editName(): 
    try: 
        data = request.get_json() 
        printerid = data['printerid']
        name = data['newname']
        fabricator_list.getFabricatorByHwid()
        res = fabricator_list.editName(printerid, name)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@status_bp.route("/serverVersion", methods=["GET"])
def getVersion():
    res = jsonify(os.environ.get('SERVER_VERSION'))
    return res