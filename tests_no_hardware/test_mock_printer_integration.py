from unittest.mock import patch

from fake_printer import (
    FakeSerialConnection,
    MockableDevice
)


def test_printer_diagnosis_without_physical_printer():

    fake_serial = FakeSerialConnection(
        responses=[b"ok\n"]
    )


    device = MockableDevice(connection=None)


    with patch(
        "Classes.Fabricators.Device."
        "FabricatorConnection.staticCreateConnection",
        return_value=fake_serial
    ) as create_connection:

        response = device.diagnose()


    create_connection.assert_called_once()

    assert b"M115\n" in fake_serial.writes

    assert response == "ok"