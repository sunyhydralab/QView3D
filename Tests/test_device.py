import os
import sys
import pytest

from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Vector3 import Vector3

def device_setup(port):
    if not port: return None
    return Fabricator.createDevice(Ports.getPortByName(port), consoleLogger=sys.stdout)


from parallel_test_runner import testLevel
testLevelToRun = testLevel
shortTest = True
device = Fabricator.createDevice(None, consoleLogger=sys.stdout)

def __desc__():
    return "Device Tests"

def __repr__():
    return f"test_device.py running on port {Ports.getPortByName(os.getenv('PORT'))}"

@pytest.fixture(scope="module", autouse=True)
def function_setup(request):
    global device
    device = device_setup(request.session.config.port)
    if device is None:
        pytest.skip("No port specified")
    device.connect()
    yield
    device.disconnect()

@pytest.mark.dependency()
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_connection():
    assert device is not None, f"No printer connected on {device.DESCRIPTION}"


@pytest.mark.dependency(depends=["test_connection"])
@pytest.mark.skipif(condition=testLevelToRun < 3, reason="Not doing lvl 3 tests")
def test_home():
    assert device.home(), f"Failed to home {device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_square():
    squarePasses = 0
    for point in [Vector3(50.0, 50.0, 2.0), Vector3(200.0, 50.0, 2.0), Vector3(200.0, 150.0, 2.0),
                  Vector3(50.0, 150.0, 2.0)]:
        squarePasses += 1 if device.goTo(point, isVerbose=True) else 0
    assert squarePasses == 4, f"Failed to draw square on {device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_octagon():
    octagonPasses = 0
    for point in [Vector3(50.0, 100.0, 2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0, 50.0, 2.0),
                  Vector3(200.0, 100.0, 2), Vector3(200.0, 150.0, 2.0), Vector3(150.0, 200.0, 2),
                  Vector3(100.0, 200.0, 2.0), Vector3(50.0, 150.0, 2.0)]:
        octagonPasses += 1 if device.goTo(point) else 0
    assert octagonPasses == 8, f"Failed to draw octagon on {device.DESCRIPTION}"

@pytest.mark.dependency(depends=["test_home"])
@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_center():
    assert device.goTo(Vector3(125.0, 100.0, 2.0)), f"Failed to go to location on {device.DESCRIPTION}"