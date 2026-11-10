from unittest.mock import MagicMock

from fake_printer import MockableDevice


def test_send_gcode_writes_to_mock_connection():

    fake_serial = MagicMock()


    fake_serial.is_open = True

    device = MockableDevice(connection=fake_serial)

    result = device.sendGcode(b"G28\n")

    assert result is True


    fake_serial.write.assert_called_once_with(b"G28\n")