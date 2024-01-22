# get connected serial ports
import serial
import serial.tools.list_ports
import time
from flask_cors import cross_origin
from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request, make_response
from models.printers import Printer

ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports",  methods=["GET", "OPTIONS"])
def getPorts():
    ports = serial.tools.list_ports.comports()
    printerList = []
    for port in ports:
        port_info = {
            'device': port.device,
            'description': port.description,
            'hwid': port.hwid,
        }
        supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
        # if port.description in supportedPrinters:
        printerList.append(port_info)
    return jsonify(printerList)

@ports_bp.route("/register", methods=["POST"])
def registerPrinter(): 
    """_summary
    interface RegisteredDevice {
        device: string; 
        description: string; 
        hwid: string; 
        customname: string; 
    }
    """
    try: 
        data = request.get_json() # get json data 
        # extract data 
        device = data['printer']['device']
        description = data['printer']['description']
        hwid = data['printer']['hwid']
        customname = data['printer']['customname']
        
        res = Printer.create_printer(device=device, description=description, hwid=hwid, name=customname)
        return res
    
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Failed to register printer. Database error"}), 500
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
        