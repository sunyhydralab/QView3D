import asyncio
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
            asyncio.run(socket.send("printer_connect"))
            
            return jsonify({"message": "Emulator registered successfully"}), 200
        except Exception as e:
            print(f"Error registering emulator: {e}")
            return jsonify({"error": "Failed to register emulator"}), 500

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500