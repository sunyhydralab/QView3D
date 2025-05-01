import asyncio
import json
import threading
from time import sleep

from flask import Blueprint, jsonify, request, current_app
import os
import subprocess
from globals import background_loop

emulator_bp = Blueprint("emulator", __name__)

@emulator_bp.route('/startemulator', methods=["POST"])
def startEmulator():
    try:
        data = request.get_json()
        model = data.get('model', 'Prusa MK4')
        config = data.get('config', {})


        # Determine which printer model to instantiate
        model_id = 1  # Default to Prusa MK4
        if model == 'Ender 3':
            model_id = 2

        # Get root path for proper execution
        from globals import root_path
        emu_path = os.path.abspath(os.path.join(root_path, "printeremu"))
        cmd = "./cmd/test_printer.go"
        emu_cmd = "-conn"

        # Run the Go emulator as a background process
        try:
            process = subprocess.Popen(
                ["go", "run", cmd, str(model_id), emu_cmd],
                cwd=emu_path,
            )
            # Wait for the process to settle
            threading.Thread(target=process.wait).start()  # Start a thread to wait for the process
            sleep(1)
            print(f"Emulator process started with PID: {process.pid}")
        except FileNotFoundError:
            print("Go command not found. Ensure Go is installed and available in PATH.")
            return jsonify({"message": "Go command not found"}), 500

        socket = next(iter(current_app.emulator_connections.values()), None)
        if not socket:
            print("No emulator connection found")  # More detailed logging
            return jsonify({"message": "No emulator connection found"}), 404

        try:
            print("Starting registration process")
            message = {
                'event': 'printer_connect',
                'data': 'start_from_front'
            }

            json_message = json.dumps(message)

            print("last before sending")
            future = asyncio.run_coroutine_threadsafe(socket.send(json_message), background_loop)
            future.result()  # block until the message is sent
            print(f"Sent start message: {json_message}")  # Log sent message

            return jsonify({"message": "Emulator started successfully"}), 200
        except Exception as e:
            print(f"Error starting emulator: {e}")
            return jsonify({"error": "Failed to start emulator"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@emulator_bp.route('/registeremulator', methods=["POST"])
def registerEmulator():
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Log received data
        print(f"Current app emulator connections: {current_app.emulator_connections}")  # Log connections

        socket = next(iter(current_app.emulator_connections.values()), None)
        if not socket:
            print("No emulator connection found")  # More detailed logging
            return jsonify({"error": "No emulator connection found"}), 404

        try:
            message = {
                'event': 'printer_connect',
                'data': 'register_from_front'
            }

            json_message = json.dumps(message)

            # Send the message to the emulator
            print("last before sending")

            future = asyncio.run_coroutine_threadsafe(socket.send(json_message), background_loop)
            future.result()  # block until the message is sent
            sleep(1)
            print(f"Sent registration message: {json_message}")  # Log sent message

            # TODO: add to db
            # # add emulator to the db
            # from server.Classes.Fabricators.Fabricator import Fabricator
            # Fabricator(
            #     port=
            # )

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


