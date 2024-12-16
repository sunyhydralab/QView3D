from flask import Blueprint, jsonify, request
import os
from globals import current_app as app
from traceback import format_exc
status_bp = Blueprint("status", __name__)

@status_bp.route('/getprinters', methods=["GET"])
def getPrinters():
    try:
        printers = app.fabricator_list.fabricators  # call the method on the instance
        return jsonify({"printers": printers})
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

# this is the route that will be called by the UI to get the printers that have threads information
@status_bp.route('/getprinterinfo', methods=["GET"])
def getPrinterInfo():
    try:
        return jsonify([fab.__to_JSON__() for fab in app.fabricator_list.fabricators])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/hardreset', methods=["POST"])
def hardreset():
    try:
        data = request.get_json() # get json data
        id = data['printerid']
        res = app.fabricator_list.resetThread(id)
        return res
    except Exception as e:
        app.handle_errors_and_logging(e)
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
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json() # get json data
        printerid = data['printerid']
        res = app.fabricator_list.deleteThread(printerid)
        return res
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/editNameInThread", methods=["POST"])
def editName():
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        name = data['newname']
        return app.fabricator_list.editName(fabricator_id, name)
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/serverVersion", methods=["GET"])
def getVersion():
    res = jsonify(os.environ.get('SERVER_VERSION'))
    return res