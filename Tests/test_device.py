import os
import pytest
from Classes.Ports import Ports
from Classes.Vector3 import Vector3
from parallel_test_runner import testLevel

testLevelToRun = testLevel
shortTest = True

def __desc__():
    return "Device Tests"

def __repr__():
    return f"test_device.py running on port {Ports.getPortByName(os.getenv('PORT'))}"

@pytest.mark.dependency()
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_connection(app, fabricator):
    assert fabricator.device is not None, f"No printer connected on {fabricator.device.DESCRIPTION}"
    assert fabricator.device.serialConnection is not None, f"No serial connection on {fabricator.device.DESCRIPTION}"
    assert fabricator.device.serialConnection.isOpen(), f"Serial connection not open on {fabricator.device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_connection"])
@pytest.mark.skipif(condition=testLevelToRun < 3, reason="Not doing lvl 3 tests")
def test_home(app, fabricator):
    assert fabricator.device.home(), f"Failed to home {fabricator.device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_draw_square(app, fabricator):
    squarePasses = 0
    for point in [Vector3(50.0, 50.0, 2.0), Vector3(200.0, 50.0, 2.0), Vector3(200.0, 150.0, 2.0),
                  Vector3(50.0, 150.0, 2.0)]:
        squarePasses += 1 if fabricator.device.goTo(point, isVerbose=True) else 0
    assert squarePasses == 4, f"Failed to draw square on {fabricator.device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_draw_octagon(app, fabricator):
    octagonPasses = 0
    for point in [Vector3(50.0, 100.0, 2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0, 50.0, 2.0),
                  Vector3(200.0, 100.0, 2), Vector3(200.0, 150.0, 2.0), Vector3(150.0, 200.0, 2),
                  Vector3(100.0, 200.0, 2.0), Vector3(50.0, 150.0, 2.0)]:
        octagonPasses += 1 if fabricator.device.goTo(point) else 0
    assert octagonPasses == 8, f"Failed to draw octagon on {fabricator.device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_go_to_center(app, fabricator):
    assert fabricator.device.goTo(Vector3(125.0, 100.0, 2.0)), f"Failed to go to location on {fabricator.device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_go_to_center"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_draw_circle(app, fabricator):
    assert fabricator.device.sendGcode(b"G2 X125 Y100 I25 J0\n"), f"Failed to draw circle on {fabricator.device.DESCRIPTION}"
    assert fabricator.device.sendGcode(b"G2 X125 Y100 I-25 J0\n"), f"Failed to draw circle on {fabricator.device.DESCRIPTION}"