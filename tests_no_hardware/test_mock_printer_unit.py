from unittest.mock import MagicMock

from fake_printer import MockableDevice


def test_send_gcode_writes_to_mock_connection():
    # Create a fake serial connection using Python's built-in mocking.
    fake_serial = MagicMock()

    # QView3D checks that the connection is open before sending G-code.
    fake_serial.is_open = True

    # Give our test device the fake connection.
    device = MockableDevice(connection=fake_serial)

    # Send a basic G-code command.
    result = device.sendGcode(b"G28\n")

    # QView3D should report that sending succeeded.
    assert result is True


    fake_serial.write.assert_called_once_with(b"G28\n")