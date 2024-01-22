# get connected serial ports
import serial
import serial.tools.list_ports
import time
from flask_cors import cross_origin
from flask import Blueprint, jsonify, request, make_response


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
