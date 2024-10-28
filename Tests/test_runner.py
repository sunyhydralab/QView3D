from datetime import datetime
import pytest
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Vector3 import Vector3
from Mixins.canPause import canPause

testLevelToRun = 5

@pytest.fixture(scope="module")
def test_setup():
    fabricators = []
    for port in ["COM3", "COM4", "COM5", "COM6", "COM7"]:
        if Ports.getPortByName(port) is not None:
            fabricators.append(Fabricator(Ports.getPortByName(port), "Test Printer", addToDB=False))
    yield fabricators

    for fabricator in fabricators:
        fabricator.device.disconnect()

@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_connection(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        assert fabricator.device is not None, f"No printer connected on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 3, reason="Not doing lvl 3 tests")
def test_home(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        assert fabricator.device.home(isVerbose=False), f"Failed to home {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_square(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        squarePasses = 0
        for point in [Vector3(50.0,50.0,2.0), Vector3(200.0,50.0,2.0), Vector3(200.0,150.0,2.0), Vector3(50.0,150.0,2.0)]:
            squarePasses += 1 if fabricator.device.goTo(point) else 0
        assert squarePasses == 4, f"Failed to draw square on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_octagon(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        octagonPasses = 0
        for point in [Vector3(50.0,100.0,2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0,50.0,2.0), Vector3(200.0, 100.0, 2), Vector3(200.0,150.0,2.0), Vector3(150.0, 200.0, 2), Vector3(100.0,200.0,2.0), Vector3(50.0, 150.0, 2.0)]:
            octagonPasses += 1 if fabricator.device.goTo(point) else 0
        assert octagonPasses == 8, f"Failed to draw octagon on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
def test_center(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        assert fabricator.device.goTo(Vector3(125.0,100.0,2.0)), f"Failed to go to center on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
def test_pause(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        if not isinstance(fabricator.device, canPause):
            continue
        assert fabricator.device.pause(), f"Failed to pause on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
def test_resume(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        if not isinstance(fabricator.device, canPause):
            continue
        assert fabricator.device.resume(), f"Failed to resume on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
def test_cancel(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        assert fabricator.cancel(), f"Failed to cancel on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
def test_status(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        assert fabricator.getStatus(), f"Failed to get status on {fabricator.getDescription()}"

@pytest.mark.skipif(condition=testLevelToRun < 9, reason="Not doing lvl 9 tests")
def test_gcode(test_setup):
    fabricators = test_setup
    for fabricator in fabricators:
        expectedTime = 2040 # for my personal home test, 1072
        expectedMinutes, expectedSeconds = divmod(expectedTime, 60)
        time = datetime.now()
        assert fabricator.device.parseGcode("20mm_calibration.gcode"), f"Failed to parse Gcode on {fabricator.getDescription()}"
        time = datetime.now() - time
        minutes, seconds = divmod(time.seconds, 60)
        assert abs(expectedTime - time.seconds) < 60, f"Failed to print within 1 minute of expected time on {fabricator.getDescription()}. Expected: {int(expectedMinutes):02}:{int(expectedSeconds):02}, Actual: {int(minutes):02}:{int(seconds):02}"
