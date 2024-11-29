from flask import Blueprint, jsonify, request
import os
from app import app, handle_errors_and_logging
from traceback import format_exc
status_bp = Blueprint("status", __name__)

@status_bp.route('/ping', methods=["GET"])
def getStatus():
    try:
        return jsonify({"status": "pong"}), 200
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/getopenthreads', methods=["GET"])
def getOpenThreads():
    try:
        open_threads = app.fabricator_list.getOpenThreads()
        return jsonify(open_threads), 200
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/getprinters', methods=["GET"])
def getPrinters():
    try:
        printers = app.fabricator_list.fabricators  # call the method on the instance
        return jsonify({"printers": printers})
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

# this is the route that will be called by the UI to get the printers that have threads information
@status_bp.route('/getprinterinfo', methods=["GET"])
def getPrinterInfo():
    try:
        return jsonify([fab.__to_JSON__() for fab in app.fabricator_list.fabricators])
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/hardreset', methods=["POST"])
def hardreset():
    try:
        data = request.get_json() # get json data
        id = data['printerid']
        res = app.fabricator_list.resetThread(id)
        return res
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/queuerestore', methods=["POST"])
def queueRestore():
    try:
        data = request.get_json() # get json data
        id = data['printerid']
        status = data['status']
        res = app.fabricator_list.queueRestore(id, status)
        return res
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        res = app.fabricator_list.deleteThread(printerid)
        return res
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/editNameInThread", methods=["POST"])
def editName():
    try:
        data = request.get_json()
        printerid = data['printerid']
        name = data['newname']
        app.fabricator_list.getFabricatorByHwid()
        res = app.fabricator_list.editName(printerid, name)
        return res
    except Exception as e:
        handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/serverVersion", methods=["GET"])
def getVersion():
    res = jsonify(os.environ.get('SERVER_VERSION'))
    return res