import asyncio
import json
import os
import random
import subprocess
import time
from flask import Blueprint, jsonify, request, current_app
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.FabricatorConnection import EmuListPortInfo, SocketConnection
from globals import emulator_connections

emulator_bp = Blueprint("emulator", __name__)

@emulator_bp.route('/startemulator', methods=["POST"])
def startEmulator():
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        config = data.get('config', {})
        
        print(f"Starting emulator for model: {model}")
        
        # Determine which printer model to instantiate
        model_id = 1  # Default to Prusa MK4
        if model == 'Ender 3':
            model_id = 2
            
        # Get root path for proper execution
        from globals import root_path
        emu_path = os.path.abspath(os.path.join(root_path, "printeremu", "cmd", "test_printer.go"))
        
        # Run the Go emulator as a background process
        try:
            process = subprocess.Popen(
                ["go", "run", emu_path, str(model_id), "-conn"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a short time for the emulator to start up
            return jsonify({"message": "Emulator process started successfully"}), 200
            
        except Exception as e:
            print(f"Error starting emulator process: {e}")
            return jsonify({"error": f"Failed to start emulator: {str(e)}"}), 500
        
    except Exception as e:
        print(f"Unexpected error in startEmulator: {e}")
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500

@emulator_bp.route('/registeremulator', methods=["POST"])
def registerEmulator():
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        config = data.get('config', {})
        
        print(f"Received data: {data}")  # Log received data
        print(f"Current emulator connections: {emulator_connections}")  # Log connections

        socket = next(iter(emulator_connections.values()), None)
        if not socket:
            print("No emulator connection found")  # More detailed logging
            return jsonify({"error": "No emulator connection found"}), 404

        # Setup emulator port
        port = config.get('port', f"EMU{random.randint(1, 999):03d}")
        name = config.get('name', "Emulator Printer")
        hwid = config.get('hwid', f"USB VID:PID=1D50:614D LOCATION=EMU-{random.randint(1, 9999)}")
        
        # Make sure socket has the necessary attributes
        socket.fake_port = port
        socket.fake_name = name
        socket.fake_hwid = hwid
        
        # Create a port object for the emulator
        emu_port = EmuListPortInfo(port, description="Emulator", hwid=hwid)
        
        # Store this information in the database for persistence
        from models.printers import Printer
        from models.db import db
        
        # Check if printer already exists in the database
        existing_printer = Printer.query.filter_by(port=port).first()
        if not existing_printer:
            # Create a new printer record
            printer_db = Printer(
                name=name,
                description=f"Emulator - {model}",
                port=port,
                hwid=hwid,
                status="ready"
            )
            db.session.add(printer_db)
            db.session.commit()
            print(f"Added emulator to database with ID: {printer_db.id}")
        
        # Register the emulator with the system
        try:
            # First, send message to the emulator
            message = {
                'event': 'printer_connect',
                'data': 'register_from_front'
            }
            
            json_message = json.dumps(message)
            asyncio.run(socket.send(json_message))
            
            # Then, add the fabricator to the system if needed
            existing_fabricator = current_app.fabricator_list.getFabricatorByPort(emu_port.device)
            
            if not existing_fabricator:
                # Create a new fabricator for the emulator
                fabricator = current_app.fabricator_list.addFabricator(emu_port, name)
                
                # Emit socket event to notify clients about the new printer
                current_app.socketio.emit('emulator_registered', {
                    'name': name,
                    'id': fabricator.id if fabricator else None
                })
                
                # Also emit the general fabricator_registered event for Dashboard
                if fabricator:
                    current_app.socketio.emit('fabricator_registered', fabricator.to_dict())
                
            return jsonify({"message": "Emulator registered successfully"}), 200
        except Exception as e:
            print(f"Error registering emulator: {e}")
            return jsonify({"error": f"Failed to register emulator: {str(e)}"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500

@emulator_bp.route('/disconnectemulator', methods=["POST"])
def disconnectEmulator():
    try:
        data = request.get_json()
        printer_config = data.get('printerConfig', {})
        port = printer_config.get('port', None)
        
        # Remove from database if it exists
        if port:
            from models.printers import Printer
            from models.db import db
            printer_db = Printer.query.filter_by(port=port).first()
            if printer_db:
                # Get the printer ID before deleting
                printer_id = printer_db.id
                db.session.delete(printer_db)
                db.session.commit()
                # Emit disconnection event
                current_app.socketio.emit('fabricator_disconnected', {'id': printer_id})
                print(f"Removed emulator from database, ID: {printer_id}")

        # Get the socket connection
        socket = next(iter(emulator_connections.values()), None)
        if not socket:
            return jsonify({"message": "No active emulator connection to disconnect"}), 200

        try:
            message = {
                'event': 'printer_disconnect',
                'data': 'disconnect_from_front'
            }

            json_message = json.dumps(message)
            asyncio.run(socket.send(json_message))
            
            # Clean up the connection from our tracking
            client_id = next(iter(emulator_connections.keys()), None)
            if client_id:
                del emulator_connections[client_id]
                print(f"Removed client {client_id} from emulator_connections")

            return jsonify({"message": "Emulator disconnected successfully"}), 200
        except Exception as e:
            print(f"Error disconnecting emulator: {e}")
            return jsonify({"error": f"Failed to disconnect emulator: {str(e)}"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500

@emulator_bp.route('/setemulatortemperature', methods=["POST"])
def setEmulatorTemperature():
    try:
        data = request.get_json()
        extruder_temp = data.get('extruder', 0)
        bed_temp = data.get('bed', 0)
        
        socket = next(iter(emulator_connections.values()), None)
        if not socket:
            return jsonify({"error": "No emulator connection found"}), 404
            
        message = {
            'event': 'set_temperature',
            'data': {
                'extruder': extruder_temp,
                'bed': bed_temp
            }
        }
        
        json_message = json.dumps(message)
        asyncio.run(socket.send(json_message))
        
        # Emit a temperature update event to all clients
        current_app.socketio.emit('emulator_temperature', {
            'extruder': extruder_temp,
            'bed': bed_temp,
            'targetExtruder': extruder_temp,
            'targetBed': bed_temp
        })
        
        return jsonify({"message": "Temperature set successfully"}), 200
        
    except Exception as e:
        print(f"Error setting temperature: {e}")
        return jsonify({"error": f"Failed to set temperature: {str(e)}"}), 500

@emulator_bp.route('/runemulatortest', methods=["POST"])
def runEmulatorTest():
    try:
        data = request.get_json()
        test_type = data.get('type', 'simple_move')
        
        socket = next(iter(emulator_connections.values()), None)
        if not socket:
            return jsonify({"error": "No emulator connection found"}), 404
            
        # Simple G-code sequence for testing
        gcode_commands = []
        
        if test_type == 'simple_move':
            gcode_commands = [
                "G28 ; Home all axes",
                "G0 Z5 ; Raise Z",
                "G0 X50 Y50 F3000 ; Move to position",
                "G0 X100 Y100 ; Move to next position",
                "G0 X50 Y100 ; Move to next position",
                "G0 X50 Y50 ; Return to start"
            ]
        elif test_type == 'temperature':
            gcode_commands = [
                "M104 S200 ; Set extruder temp",
                "M140 S60 ; Set bed temp",
                "M105 ; Report temperatures"
            ]
        
        # Send each command
        for command in gcode_commands:
            message = {
                'event': 'send_gcode',
                'data': {
                    'printerid': '1',  # Default printer ID
                    'gcode': command
                }
            }
            
            json_message = json.dumps(message)
            asyncio.run(socket.send(json_message))
            # Use sleep instead of asyncio.sleep to avoid async issues
            time.sleep(0.1)
        
        return jsonify({"message": "Test commands sent successfully"}), 200
        
    except Exception as e:
        print(f"Error running test: {e}")
        return jsonify({"error": f"Failed to run test: {str(e)}"}), 500

@emulator_bp.route('/resetemulator', methods=["POST"])
def resetEmulator():
    try:
        socket = next(iter(emulator_connections.values()), None)
        if not socket:
            return jsonify({"error": "No emulator connection found"}), 404
            
        message = {
            'event': 'reset_emulator',
            'data': {}
        }
        
        json_message = json.dumps(message)
        asyncio.run(socket.send(json_message))
        
        # Update clients about the reset
        current_app.socketio.emit('emulator_status', {
            'status': 'Reset',
            'message': 'Emulator has been reset'
        })
        
        # Reset temperatures
        current_app.socketio.emit('emulator_temperature', {
            'extruder': 25,
            'bed': 25,
            'targetExtruder': 0,
            'targetBed': 0
        })
        
        return jsonify({"message": "Emulator reset successfully"}), 200
        
    except Exception as e:
        print(f"Error resetting emulator: {e}")
        return jsonify({"error": f"Failed to reset emulator: {str(e)}"}), 500
