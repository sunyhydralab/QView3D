from flask import Blueprint, jsonify, request
import os
from services.app_service import current_app as app
from traceback import format_exc
status_bp = Blueprint("status", __name__)

@status_bp.route('/getprinters', methods=["GET"])
def getPrinters():
    try:
        return jsonify({"printers": app.fabricator_list.fabricators})
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        data = request.get_json()
        return app.fabricator_list.resetThread(data['printerid'])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route('/queuerestore', methods=["POST"])
def queueRestore():
    try:
        data = request.get_json()
        return app.fabricator_list.queueRestore(data['printerid'], data['status'])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/removethread", methods=["POST"])
def removeThread():
    try:
        data = request.get_json()
        return app.fabricator_list.deleteThread(data['printerid'])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/editNameInThread", methods=["POST"])
def editName():
    try:
        data = request.get_json()
        return app.fabricator_list.editName(data['fabricator_id'], data['newname'])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@status_bp.route("/serverVersion", methods=["GET"])
def getVersion():
    return jsonify(os.environ.get('SERVER_VERSION'))

@status_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "qview3d-python-backend"}), 200