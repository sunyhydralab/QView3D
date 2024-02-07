from flask import Blueprint, jsonify
from app import printer_status_service  # import the instance from app.py

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
    printer_info = printer_status_service.retrieve_printer_info()  # call the method on the instance
    

    
    return jsonify(printer_info)