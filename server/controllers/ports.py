from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request

from globals import current_app as app
from Classes.Fabricators.Device import Device
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Ports import Ports
from traceback import format_exc

# Blueprint for ports routes
ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports", methods=["GET"])
def getPorts():
    """Get a list of all connected ports."""
    try:
        ports = Ports.getPorts()
        return jsonify([port for port in ports])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/getfabricators", methods=["GET"])
def getRegisteredFabricators():
    """Get a list of all registered fabricators."""
    try:
        fabricators = Fabricator.queryAll()
        return jsonify([fab.__to_JSON__() for fab in fabricators])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/register", methods=["POST"])
def registerFabricator():
    """Register a new fabricator with the system."""
    try:
        data = request.get_json()
        printer = data['printer']
        device = printer['device']['serialPort']
        name = printer['name']

        # Create a new fabricator instance using the Fabricator class
        try:
            app.fabricator_list.addFabricator(device, name)
        except AssertionError as ae:
            return jsonify({"error": f"Failed to add fabricator: {ae}"}), 500
        new_fabricator = Fabricator.query.filter_by(devicePort=device).first()

        return jsonify({"success": True, "message": "Fabricator registered successfully", "fabricator_id": new_fabricator.dbID})
    except SQLAlchemyError as db_err:
        print(f"Database error during registration: {db_err}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": e.args}), 500

@ports_bp.route("/deletefabricator", methods=["POST"])
def deleteFabricator():
    """Delete a fabricator from the system."""
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        res = app.fabricator_list.deleteFabricator(fabricator_id)
        if isinstance(res, ValueError):
            return jsonify({"error": "Fabricator not found"}), 404
        if res: return jsonify({"success": True, "message": "Fabricator deleted successfully"})
        return jsonify({"error": "Failed to delete fabricator"}), 500
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/editname", methods=["POST"])
def editName():
    """Edit the name of a registered fabricator."""
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        new_name = data['name']

        fabricator = Fabricator.query.filter_by(dbID=fabricator_id).first()
        if fabricator:
            fabricator.setName(new_name)
            return jsonify({"success": True, "message": "Fabricator name updated successfully"})
        else:
            return jsonify({"error": "Fabricator not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/diagnose", methods=["POST"])
def diagnoseFabricator():
    """Diagnose a fabricator based on its port."""
    try:
        data = request.get_json()
        device_name = data['device']
        port = Ports.getPortByName(device_name)
        fabricator = app.fabricator_list.getFabricatorByPort(port)
        if fabricator:
            device = fabricator.device
            if device is None:
                device = Fabricator.staticCreateDevice(port)  # Ensure the Fabricator has this method
            if device is not None:
                assert isinstance(device, Device), f"Device must be an instance of Device: {device} : {type(device)}"
                diagnosis_result = device.diagnose()
                return jsonify({"success": True, "message": "Diagnosis successful", "diagnoseString": diagnosis_result})
            else:
                return jsonify({"error": "Failed to create device for diagnosis"}), 500
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/repair", methods=["POST"])
def repairFabricator():
    """Repair a fabricator based on its port."""
    try:
        data = request.get_json()
        device_name = data['device']
        port = Ports.getPortByName(device_name)

        if port:
            fabricator = Fabricator.staticCreateDevice(port)  # Ensure the Fabricator has this method
            if fabricator:
                repair_result = fabricator.repair()
                return jsonify({"success": True, "message": repair_result})
            else:
                return jsonify({"error": "Failed to create fabricator for repair"}), 500
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/movehead", methods=["POST"])
def moveHead():
    """Move the head of a fabricator. Deprecated if no longer needed."""
    try:
        data = request.get_json()
        port = data['port']
        if port:
            if app:
                fab = app.fabricator_list.getFabricatorByPort(port)
                # print(fab if fab else f"No fabricator found in fabricator list, fabricator_list: {app.fabricator_list.fabricators}, threads: {app.fabricator_list.fabricator_threads}")
                if fab: 
                    device = fab.device
                elif port.startswith("EMU"):
                    device = Fabricator.staticCreateDevice(Ports.getPortByName(port), websocket_connection=next(iter(app.emulator_connections.values())))
                else:
                    device = Fabricator.staticCreateDevice(Ports.getPortByName(port)) 
            else: 
                device = Fabricator(port).device
            device.connect()
            result = device.home(isVerbose=False)  # Use home() method from Device
            device.disconnect()
            return jsonify({"success": True, "message": "Head move successful"}) if result else jsonify({"success": False, "message": "Head move unsuccessful"})
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/movefabricatorlist", methods=["POST"])
def moveFabricatorList():
    """Change the order of fabricators."""
    try:
        data = request.get_json()
        fabricator_ids = data['fabricator_ids']
        result = app.fabricator_list.moveFabricatorList(fabricator_ids)
        return jsonify({"success": True, "message": "Fabricator list successfully updated"}) if result != "none" else jsonify({"success": False, "message": "Fabricator list not updated"})
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/getfabricatorbyid", methods=["POST"])
def getFabricatorById():
    """Get a fabricator by its ID."""
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        fabricator = app.fabricator_list.getFabricatorByID(fabricator_id)
        if fabricator:
            return jsonify({"success": True, "fabricator": fabricator.__to_JSON__()})
        else:
            return jsonify({"error": "Fabricator not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500
