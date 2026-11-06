from unittest.mock import patch

from fake_printer import (
    FakeSerialConnection,
    MockableDevice
)


def test_printer_diagnosis_without_physical_printer():
    # Our fake printer will respond "ok".
    fake_serial = FakeSerialConnection(
        responses=[b"ok\n"]
    )

    # Start with no connection.
    device = MockableDevice(connection=None)

    # Replace QView3D's real serial-connection creation
    # with our fake connection.
    with patch(
        "Classes.Fabricators.Device."
        "FabricatorConnection.staticCreateConnection",
        return_value=fake_serial
    ) as create_connection:

        response = device.diagnose()

    # Verify QView3D tried to create a printer connection.
    create_connection.assert_called_once()

    # diagnose() sends M115 to the printer.
    assert b"M115\n" in fake_serial.writes

    # Our fake printer returned "ok".
    assert response == "ok"