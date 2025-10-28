from flask import Blueprint, jsonify, request
from services.app_service import current_app
from Classes.Fabricators.Fabricator import Fabricator
from config.db import db
import random
import string

emulator_bp = Blueprint("emulator", __name__)

def generate_mock_serial():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@emulator_bp.route('/emulator/create', methods=["POST"])
def createMockPrinter():
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        name = data.get('name', f'Mock {model}')
        mock_port = f"EMU_{generate_mock_serial()}"

        existing = Fabricator.query.filter_by(devicePort=mock_port).first()
        if existing:
            return jsonify({"error": "Mock printer with this port already exists"}), 400

        try:
            app = current_app
            if hasattr(app, 'fabricator_list'):
                app.fabricator_list.addFabricator(mock_port, name)
                created_fab = Fabricator.query.filter_by(devicePort=mock_port).first()
                if created_fab:
                    created_fab.model = model
                    db.session.commit()
            else:
                new_fabricator = Fabricator(devicePort=mock_port, name=name)
                new_fabricator.model = model
                new_fabricator.status = "ready"
                db.session.add(new_fabricator)
                db.session.commit()
                created_fab = new_fabricator

            return jsonify({
                "success": True,
                "message": "Mock printer created successfully",
                "port": mock_port,
                "printer": {
                    "id": created_fab.dbID,
                    "name": created_fab.name,
                    "model": model,
                    "port": mock_port,
                    "status": "ready"
                }
            }), 200
        except Exception as e:
            print(f"Error creating mock printer: {e}")
            return jsonify({"error": f"Failed to create mock printer: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500

@emulator_bp.route('/emulator/list', methods=["GET"])
def listMockPrinters():
    try:
        mock_printers = Fabricator.query.filter(Fabricator.devicePort.like('EMU_%')).all()
        printers_list = [{
            "id": printer.dbID,
            "name": printer.name,
            "model": getattr(printer, 'model', 'Unknown'),
            "port": printer.devicePort,
            "status": getattr(printer, 'status', 'unknown')
        } for printer in mock_printers]
        return jsonify(printers_list), 200
    except Exception as e:
        print(f"Error listing mock printers: {e}")
        return jsonify({"error": "Failed to list mock printers"}), 500

@emulator_bp.route('/emulator/delete/<int:printer_id>', methods=["DELETE"])
def deleteMockPrinter(printer_id):
    try:
        fabricator = Fabricator.query.filter_by(dbID=printer_id).first()
        if not fabricator:
            return jsonify({"error": "Printer not found"}), 404
        if not fabricator.devicePort.startswith('EMU_'):
            return jsonify({"error": "Can only delete mock printers"}), 400

        app = current_app
        if hasattr(app, 'fabricator_list'):
            app.fabricator_list.deleteFabricator(printer_id)
        else:
            db.session.delete(fabricator)
            db.session.commit()

        return jsonify({"message": "Mock printer deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting mock printer: {e}")
        return jsonify({"error": f"Failed to delete mock printer: {str(e)}"}), 500

@emulator_bp.route('/emulator/update_status/<int:printer_id>', methods=["POST"])
def updateMockPrinterStatus(printer_id):
    try:
        data = request.get_json()
        new_status = data.get('status', 'ready')
        valid_statuses = ['ready', 'printing', 'paused', 'error', 'offline', 'maintenance']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        fabricator = Fabricator.query.filter_by(dbID=printer_id).first()
        if not fabricator:
            return jsonify({"error": "Printer not found"}), 404
        if not fabricator.devicePort.startswith('EMU_'):
            return jsonify({"error": "Can only update status of mock printers"}), 400

        fabricator.status = new_status
        db.session.commit()

        if hasattr(current_app, 'socketio'):
            current_app.socketio.emit('printer_status_update', {
                'printer_id': printer_id,
                'status': new_status
            })

        return jsonify({
            "message": "Status updated successfully",
            "printer_id": printer_id,
            "new_status": new_status
        }), 200
    except Exception as e:
        print(f"Error updating mock printer status: {e}")
        return jsonify({"error": f"Failed to update status: {str(e)}"}), 500

@emulator_bp.route('/startemulator', methods=["POST"])
def startEmulator():
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        config = data.get('config', {})
        name = config.get('name', f'Virtual Printer')
        mock_port = f"EMU_{generate_mock_serial()}"

        existing = Fabricator.query.filter_by(devicePort=mock_port).first()
        if existing:
            return jsonify({"error": "Mock printer with this port already exists"}), 400

        try:
            app = current_app
            if hasattr(app, 'fabricator_list'):
                app.fabricator_list.addFabricator(mock_port, name)
                created_fab = Fabricator.query.filter_by(devicePort=mock_port).first()
                if created_fab:
                    created_fab.model = model
                    db.session.commit()
            else:
                new_fabricator = Fabricator(devicePort=mock_port, name=name)
                new_fabricator.model = model
                new_fabricator.status = "ready"
                db.session.add(new_fabricator)
                db.session.commit()
                created_fab = new_fabricator

            if hasattr(current_app, 'socketio') and created_fab:
                current_app.socketio.emit('fabricator_registered', created_fab.__to_JSON__())

            return jsonify({
                "success": True,
                "message": "Emulator started successfully",
                "port": mock_port,
                "printer": {
                    "id": created_fab.dbID if created_fab else None,
                    "name": name,
                    "model": model,
                    "port": mock_port,
                    "status": "ready"
                }
            }), 200
        except Exception as e:
            print(f"Error creating emulator: {e}")
            return jsonify({"success": False, "error": f"Failed to create emulator: {str(e)}"}), 500
    except Exception as e:
        print(f"Unexpected error in startEmulator: {e}")
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

@emulator_bp.route('/registeremulator', methods=["POST"])
def registerEmulator():
    try:
        data = request.get_json()
        config = data.get('config', {})
        port = config.get('port', '')

        if port:
            fabricator = Fabricator.query.filter_by(devicePort=port).first()
            if fabricator:
                return jsonify({
                    "success": True,
                    "message": "Emulator already registered",
                    "printer": {
                        "id": fabricator.dbID,
                        "name": fabricator.name,
                        "port": fabricator.devicePort,
                        "status": getattr(fabricator, 'status', 'unknown')
                    }
                }), 200

        return jsonify({"success": True, "message": "Emulator registration acknowledged"}), 200
    except Exception as e:
        print(f"Error in registerEmulator: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@emulator_bp.route('/disconnectemulator', methods=["POST"])
def disconnectEmulator():
    return jsonify({"success": True, "message": "Emulator disconnected (no-op for mock printers)"}), 200