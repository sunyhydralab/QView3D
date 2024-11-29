import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from Classes.Fabricators.Fabricator import Fabricator
from Classes.serialCommunication import sendGcode

class Ports:
    @staticmethod
    def getPorts() -> list[ListPortInfo | SysFS]:
        """Get a list of all connected serial ports."""
        return serial.tools.list_ports.comports()

    @staticmethod
    def getPortByName(name: str) -> ListPortInfo | SysFS | None:
        """Get a specific port by its device name."""
        assert isinstance(name, str), f"Name must be a string: {name} : {type(name)}"
        ports = Ports.getPorts()
        for port in ports:
            if port.device == name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str) -> ListPortInfo | SysFS | None:
        """Get a specific port by its hardware ID."""
        assert isinstance(hwid, str), f"HWID must be a string: {hwid} : {type(hwid)}"
        ports = Ports.getPorts()
        for port in ports:
            if hwid in port.hwid:
                return port
        return None

    @staticmethod
    def getRegisteredFabricators() -> list[Fabricator]:
        """Get a list of all registered fabricators."""
        fabricators = Fabricator.queryAll()
        registered_fabricators = []
        for fab in fabricators:
            port = Ports.getPortByName(fab.devicePort)
            if port:
                registered_fabricators.append(fab)
        return registered_fabricators

    @staticmethod
    def diagnosePort(port: ListPortInfo | SysFS) -> str:
        """Diagnose a port to check if it is functional by sending basic G-code commands."""
        try:
            device = Fabricator.createDevice(port)
            if not device:
                return "Device creation failed."

            device.connect()
            sendGcode("M115")
            response = device.getSerialConnection().readline().decode("utf-8").strip()
            device.disconnect()

            return f"Diagnosis result for {port.device}: {response}"
        except Exception as e:
            return f"Error diagnosing port {port.device}: {e}"

# Blueprint for ports routes
ports_bp = Blueprint("ports", __name__)

@ports_bp.route("/getports", methods=["GET"])
def getPorts():
    """Get a list of all connected ports."""
    try:
        ports = Ports.getPorts()
        return jsonify([port.device for port in ports])
    except Exception as e:
        print(f"Error getting ports: {e}")
        return jsonify({"error": "Failed to retrieve ports"}), 500

@ports_bp.route("/getfabricators", methods=["GET"])
def getRegisteredFabricators():
    """Get a list of all registered fabricators."""
    try:
        fabricators = Ports.getRegisteredFabricators()
        return jsonify([{
            "name": fab.name,
            "description": fab.description,
            "hwid": fab.hwid,
            "devicePort": fab.devicePort,
            "status": fab.getStatus()
        } for fab in fabricators])
    except Exception as e:
        print(f"Error getting registered fabricators: {e}")
        return jsonify({"error": "Failed to retrieve registered fabricators"}), 500

@ports_bp.route("/register", methods=["POST"])
def registerFabricator():
    """Register a new fabricator with the system."""
    try:
        data = request.get_json()
        device = data['fabricator']['device']
        description = data['fabricator']['description']
        hwid = data['fabricator']['hwid']
        name = data['fabricator']['name']

        new_fabricator = Fabricator(Ports.getPortByName(device), name)
        new_fabricator.description = description
        new_fabricator.hwid = hwid

        return jsonify({"success": True, "message": "Fabricator registered successfully", "fabricator_id": new_fabricator.dbID})
    except SQLAlchemyError as db_err:
        print(f"Database error during registration: {db_err}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"Error registering fabricator: {e}")
        return jsonify({"error": "Failed to register fabricator"}), 500

@ports_bp.route("/deletefabricator", methods=["POST"])
def deleteFabricator():
    """Delete a fabricator from the system."""
    try:
        data = request.get_json()
        fabricator_id = data['fabricator_id']
        fabricator = Fabricator.query.filter_by(dbID=fabricator_id).first()

        if fabricator:
            Fabricator.query.filter_by(dbID=fabricator_id).delete()
            Fabricator.updateDB()
            return jsonify({"success": True, "message": "Fabricator deleted successfully"})
        else:
            return jsonify({"error": "Fabricator not found"}), 404
    except Exception as e:
        print(f"Error deleting fabricator: {e}")
        return jsonify({"error": "Failed to delete fabricator"}), 500

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
        print(f"Error editing fabricator name: {e}")
        return jsonify({"error": "Failed to edit fabricator name"}), 500

@ports_bp.route("/diagnose", methods=["POST"])
def diagnoseFabricator():
    """Diagnose a fabricator based on its port."""
    try:
        data = request.get_json()
        device_name = data['device']
        port = Ports.getPortByName(device_name)

        if port:
            diagnosis_result = Ports.diagnosePort(port)
            return jsonify({"success": True, "message": diagnosis_result})
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        print(f"Error diagnosing fabricator: {e}")
        return jsonify({"error": "Failed to diagnose fabricator"}), 500

@ports_bp.route("/movehead", methods=["POST"])
def moveHead():
    """Move the head of a fabricator. Deprecated??????"""
    try:
        data = request.get_json()
        device_name = data['port']
        port = Ports.getPortByName(device_name)

        if port:
            fabricator = Fabricator(port)
            result = fabricator.device.home()  # Ensuring `home()` method from Device is used
            return jsonify({"success": True, "message": "Head move successful"}) if result else jsonify({"success": False, "message": "Head move unsuccessful"})
        else:
            return jsonify({"error": "Device not found"}), 404
    except Exception as e:
        print(f"Error moving head: {e}")
        return jsonify({"error": "Failed to move fabricator head"}), 500

@ports_bp.route("/movefabricatorlist", methods=["POST"])
def moveFabricatorList():
    """Change the order of fabricators."""
    try:
        data = request.get_json()
        fabricator_ids = data['fabricator_ids']
        from app import fabricator_list
        result = fabricator_list.moveFabricatorList(fabricator_ids)
        return jsonify({"success": True, "message": "Fabricator list successfully updated"}) if result != "none" else jsonify({"success": False, "message": "Fabricator list not updated"})
    except Exception as e:
        print(f"Error moving fabricator list: {e}")
        return jsonify({"error": "Failed to move fabricator list"}), 500