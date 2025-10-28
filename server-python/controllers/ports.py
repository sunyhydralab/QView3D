from sqlalchemy.exc import SQLAlchemyError
from flask import Blueprint, jsonify, request
from services.app_service import current_app as app
from Classes.Fabricators.Device import Device
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Ports import Ports
from traceback import format_exc

ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports", methods=["GET"])
def getPorts():
    try:
        return jsonify([port for port in Ports.getPorts()])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/getfabricators", methods=["GET"])
def getRegisteredFabricators():
    try:
        return jsonify([fab.__to_JSON__() for fab in Fabricator.queryAll()])
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/register", methods=["POST"])
def registerFabricator():
    try:
        data = request.get_json()
        printer = data['printer']
        device = printer['device']['serialPort']
        name = printer['name']

        try:
            app.fabricator_list.addFabricator(device, name)
        except AssertionError as ae:
            return jsonify({"error": f"Failed to add fabricator: {ae}"}), 500
        except Exception as e:
            print(f"Error adding fabricator: {e}")
            return jsonify({"error": str(e)}), 500

        device_port_name = device.strip("/").split("/")[-1]
        new_fabricator = Fabricator.query.filter_by(devicePort=device_port_name).first()

        if not new_fabricator:
            return jsonify({"error": "Fabricator was not created in database"}), 500

        if app.socketio:
            app.socketio.emit('fabricator_registered', new_fabricator.__to_JSON__())

        return jsonify({"success": True, "message": "Fabricator registered successfully", "fabricator_id": new_fabricator.dbID})
    except SQLAlchemyError as db_err:
        print(f"Database error during registration: {db_err}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": str(e)}), 500

@ports_bp.route("/deletefabricator", methods=["POST"])
def deleteFabricator():
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        res = app.fabricator_list.deleteFabricator(fabricator_id)
        if isinstance(res, ValueError):
            return jsonify({"error": "Fabricator not found"}), 404

        if res:
            if app.socketio:
                app.socketio.emit('fabricator_disconnected', {'id': fabricator_id})
            return jsonify({"success": True, "message": "Fabricator deleted successfully"})

        return jsonify({"error": "Failed to delete fabricator"}), 500
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/editname", methods=["POST"])
def editName():
    try:
        data = request.get_json()
        fabricator = Fabricator.query.filter_by(dbID=data['fabricator_id']).first()
        if fabricator:
            fabricator.setName(data['name'])
            return jsonify({"success": True, "message": "Fabricator name updated successfully"})
        else:
            return jsonify({"error": "Fabricator not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/diagnose", methods=["POST"])
def diagnoseFabricator():
    try:
        data = request.get_json()
        port = Ports.getPortByName(data['device'])
        fabricator = app.fabricator_list.getFabricatorByPort(port)
        if fabricator:
            device = fabricator.device if fabricator.device else Fabricator.staticCreateDevice(port)
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
    try:
        data = request.get_json()
        port = Ports.getPortByName(data['device'])
        if port:
            fabricator = Fabricator.staticCreateDevice(port)
            if fabricator:
                return jsonify({"success": True, "message": fabricator.repair()})
            else:
                return jsonify({"error": "Failed to create fabricator for repair"}), 500
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/movehead", methods=["POST"])
def moveHead():
    try:
        data = request.get_json()
        port = data['port']
        if port:
            if app:
                fab = app.fabricator_list.getFabricatorByPort(port)
                if fab:
                    device = fab.device
                elif port.startswith("EMU"):
                    device = Fabricator.staticCreateDevice(Ports.getPortByName(port), websocket_connection=next(iter(app.emulator_connections.values())))
                else:
                    device = Fabricator.staticCreateDevice(Ports.getPortByName(port))
            else:
                device = Fabricator(port).device
            device.connect()
            result = device.home(isVerbose=False)
            device.disconnect()
            return jsonify({"success": True, "message": "Head move successful"}) if result else jsonify({"success": False, "message": "Head move unsuccessful"})
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/movefabricatorlist", methods=["POST"])
def moveFabricatorList():
    try:
        data = request.get_json()
        result = app.fabricator_list.moveFabricatorList(data['fabricator_ids'])
        return jsonify({"success": True, "message": "Fabricator list successfully updated"}) if result != "none" else jsonify({"success": False, "message": "Fabricator list not updated"})
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/getfabricatorbyid", methods=["POST"])
def getFabricatorById():
    try:
        data = request.get_json()
        fabricator = app.fabricator_list.getFabricatorById(data['fabricator_id'])
        if fabricator:
            return jsonify({"success": True, "fabricator": fabricator.__to_JSON__()})
        else:
            return jsonify({"error": "Fabricator not found"}), 404
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@ports_bp.route("/fabricators/models", methods=["GET"])
def getFabricatorModels():
    try:
        fabricators = Fabricator.queryAll()
        models = {fab.model for fab in fabricators if hasattr(fab, 'model') and fab.model}
        if not models:
            return jsonify(['Prusa MK3', 'Prusa MK4', 'Ender 3', 'MakerBot Replicator'])
        return jsonify(sorted(list(models)))
    except Exception as e:
        app.handle_errors_and_logging(e)
        return jsonify(['Prusa MK3', 'Prusa MK4', 'Ender 3', 'MakerBot Replicator'])
