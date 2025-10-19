import json
from flask import Blueprint, jsonify, request, current_app
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Ports import Ports
from config.db import db
import random
import string

emulator_bp = Blueprint("emulator", __name__)

def generate_mock_serial():
    """Generate a mock serial number for emulated printer."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@emulator_bp.route('/api/emulator/create', methods=["POST"])
def createMockPrinter():
    """
    Create a mock printer in the database for frontend testing.
    This is a simplified version that just adds a printer to the database.
    """
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        name = data.get('name', f'Mock {model}')

        # Generate a unique mock port
        mock_serial = generate_mock_serial()
        mock_port = f"EMU_{mock_serial}"

        # Check if this port already exists
        existing = Fabricator.query.filter_by(devicePort=mock_port).first()
        if existing:
            return jsonify({"error": "Mock printer with this port already exists"}), 400

        # Create mock printer in database
        try:
            # Add to fabricator list
            app = current_app
            if hasattr(app, 'fabricator_list'):
                app.fabricator_list.addFabricator(mock_port, name)
            else:
                # Direct database insert if fabricator_list not available
                new_fabricator = Fabricator(devicePort=mock_port, name=name)
                new_fabricator.model = model
                new_fabricator.status = "ready"
                db.session.add(new_fabricator)
                db.session.commit()

            # Get the created fabricator
            created_fab = Fabricator.query.filter_by(devicePort=mock_port).first()

            return jsonify({
                "message": "Mock printer created successfully",
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

@emulator_bp.route('/api/emulator/list', methods=["GET"])
def listMockPrinters():
    """List all mock printers (those with EMU_ prefix)."""
    try:
        # Query all fabricators with EMU_ prefix
        mock_printers = Fabricator.query.filter(Fabricator.devicePort.like('EMU_%')).all()

        printers_list = []
        for printer in mock_printers:
            printers_list.append({
                "id": printer.dbID,
                "name": printer.name,
                "model": getattr(printer, 'model', 'Unknown'),
                "port": printer.devicePort,
                "status": printer.status
            })

        return jsonify(printers_list), 200

    except Exception as e:
        print(f"Error listing mock printers: {e}")
        return jsonify({"error": "Failed to list mock printers"}), 500

@emulator_bp.route('/api/emulator/delete/<int:printer_id>', methods=["DELETE"])
def deleteMockPrinter(printer_id):
    """Delete a mock printer from the database."""
    try:
        # Find the fabricator
        fabricator = Fabricator.query.filter_by(dbID=printer_id).first()

        if not fabricator:
            return jsonify({"error": "Printer not found"}), 404

        # Check if it's a mock printer
        if not fabricator.devicePort.startswith('EMU_'):
            return jsonify({"error": "Can only delete mock printers"}), 400

        # Delete from fabricator list if available
        app = current_app
        if hasattr(app, 'fabricator_list'):
            app.fabricator_list.deleteFabricator(printer_id)
        else:
            # Direct database delete
            db.session.delete(fabricator)
            db.session.commit()

        return jsonify({"message": "Mock printer deleted successfully"}), 200

    except Exception as e:
        print(f"Error deleting mock printer: {e}")
        return jsonify({"error": f"Failed to delete mock printer: {str(e)}"}), 500

@emulator_bp.route('/api/emulator/update_status/<int:printer_id>', methods=["POST"])
def updateMockPrinterStatus(printer_id):
    """Update the status of a mock printer for testing."""
    try:
        data = request.get_json()
        new_status = data.get('status', 'ready')

        # Valid statuses
        valid_statuses = ['ready', 'printing', 'paused', 'error', 'offline', 'maintenance']
        if new_status not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

        # Find the fabricator
        fabricator = Fabricator.query.filter_by(dbID=printer_id).first()

        if not fabricator:
            return jsonify({"error": "Printer not found"}), 404

        # Check if it's a mock printer
        if not fabricator.devicePort.startswith('EMU_'):
            return jsonify({"error": "Can only update status of mock printers"}), 400

        # Update status
        fabricator.status = new_status
        db.session.commit()

        # Emit status update via SocketIO if available
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

# Keep simplified versions of old endpoints for backward compatibility
@emulator_bp.route('/startemulator', methods=["POST"])
def startEmulator():
    """Legacy endpoint - redirects to create mock printer."""
    return createMockPrinter()

@emulator_bp.route('/registeremulator', methods=["POST"])
def registerEmulator():
    """Legacy endpoint - redirects to create mock printer."""
    return createMockPrinter()

@emulator_bp.route('/disconnectemulator', methods=["POST"])
def disconnectEmulator():
    """Legacy endpoint - returns success for compatibility."""
    return jsonify({"message": "Emulator disconnected (no-op for mock printers)"}), 200