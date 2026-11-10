from flask import Blueprint, current_app, jsonify
from serial.tools.list_ports_common import ListPortInfo

from Classes.Fabricators.MockPrinter import MockPrinter


emulator_bp = Blueprint("emulator", __name__)


def create_mock_port():
    port = ListPortInfo("MOCK_PORT")
    port.description = "Python Mock Printer"
    port.hwid = "MOCK_HWID"
    port.serial_number = "MOCK_SERIAL"

    return port


@emulator_bp.route("/startemulator", methods=["POST"])
def start_emulator():
    printer = MockPrinter(
        dbID=999999,
        serialPort=create_mock_port(),
        name="Mock Printer"
    )

    current_app.mock_printer = printer
    current_app.mock_printer_registered = False

    return jsonify({
        "message": "Python mock printer connected"
    }), 200


@emulator_bp.route(
    "/registeremulator",
    methods=["POST"]
)
def register_emulator():
    printer = getattr(
        current_app,
        "mock_printer",
        None
    )

    if printer is None:
        return jsonify({
            "error": "Connect the mock printer first"
        }), 400

    current_app.mock_printer_registered = True

    return jsonify({
        "message": "Python mock printer registered"
    }), 200


@emulator_bp.route(
    "/runemulatortest",
    methods=["POST"]
)
def run_emulator_test():
    printer = getattr(
        current_app,
        "mock_printer",
        None
    )

    if printer is None:
        return jsonify({
            "error": "Mock printer is not connected"
        }), 400

    if not getattr(
        current_app,
        "mock_printer_registered",
        False
    ):
        return jsonify({
            "error": "Register the mock printer first"
        }), 400

    printer.sendGcode(b"M115\n")

    response = (
        printer
        .serialConnection
        .readline()
        .decode("utf-8")
        .strip()
    )

    return jsonify({
        "command": "M115",
        "response": response
    }), 200


@emulator_bp.route(
    "/disconnectemulator",
    methods=["POST"]
)
def disconnect_emulator():
    printer = getattr(
        current_app,
        "mock_printer",
        None
    )

    if printer is not None:
        printer.disconnect()

    current_app.mock_printer = None
    current_app.mock_printer_registered = False

    return jsonify({
        "message": "Python mock printer disconnected"
    }), 200