import asyncio
import json
from flask import Blueprint, jsonify, request

emulator_bp = Blueprint("emulator", __name__)

@emulator_bp.route('/registeremulator', methods=["POST"])
def registerEmulator():
    try:
        data = request.get_json()
        
        from app import emulator_connections

        print(emulator_connections)

        socket = next(iter(emulator_connections.values()))

        try:
            message = {
                'event': 'printer_connect',
                'data': 'register_from_front'
            }
            
            json_message = json.dumps(message)
            
            asyncio.run(socket.send(json_message))
            
            return jsonify({"message": "Emulator registered successfully"}), 200
        except Exception as e:
            print(f"Error registering emulator: {e}")
            return jsonify({"error": "Failed to register emulator"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@emulator_bp.route('/disconnectemulator', methods=["POST"])
def disconnectEmulator():
    try:
        data = request.get_json()
        
        from app import emulator_connections

        print(emulator_connections)

        socket = next(iter(emulator_connections.values()))

        try:
            message = {
                'event': 'printer_disconnect',
                'data': 'disconnect_from_front'
            }
            
            json_message = json.dumps(message)
            
            asyncio.run(socket.send(json_message))
            
            return jsonify({"message": "Emulator disconnected successfully"}), 200
        except Exception as e:
            print(f"Error disconnecting emulator: {e}")
            return jsonify({"error": "Failed to disconnect emulator"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500