import os
from datetime import datetime
import re
import pytest
from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Vector3 import Vector3
from Mixins.canPause import canPause

class TestFabricator:
    testLevelToRun = 5
    shortTest = True

    @classmethod
    @pytest.fixture(scope="session", autouse=True)
    def function_setup(cls, request):
        port = os.getenv("PORT")
        if not port:
            pytest.skip("No port specified")

        fabricator_instance = Fabricator(Ports.getPortByName(port), "Test Printer", addToDB=False)

        yield fabricator_instance

        fabricator_instance.device.disconnect()

    @pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
    @pytest.mark.order(1)
    def test_connection(self, function_setup):
        fabricator = function_setup
        assert fabricator.device is not None, f"No printer connected on {fabricator.getDescription()}"

    @pytest.mark.skipif(condition=testLevelToRun < 3, reason="Not doing lvl 3 tests")
    @pytest.mark.order(2)
    def test_home(self, function_setup):
        fabricator = function_setup
        assert fabricator.device.home(isVerbose=False), f"Failed to home {fabricator.getDescription()}"

    @pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
    @pytest.mark.order(3)
    def test_square(self, function_setup):
        fabricator = function_setup
        squarePasses = 0
        for point in [Vector3(50.0, 50.0, 2.0), Vector3(200.0, 50.0, 2.0), Vector3(200.0, 150.0, 2.0),
                      Vector3(50.0, 150.0, 2.0)]:
            squarePasses += 1 if fabricator.device.goTo(point) else 0
        assert squarePasses == 4, f"Failed to draw square on {fabricator.getDescription()}"


    @pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
    @pytest.mark.order(4)
    def test_octagon(self, function_setup):
        fabricator = function_setup
        octagonPasses = 0
        for point in [Vector3(50.0, 100.0, 2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0, 50.0, 2.0),
                      Vector3(200.0, 100.0, 2), Vector3(200.0, 150.0, 2.0), Vector3(150.0, 200.0, 2),
                      Vector3(100.0, 200.0, 2.0), Vector3(50.0, 150.0, 2.0)]:
            octagonPasses += 1 if fabricator.device.goTo(point) else 0
        assert octagonPasses == 8, f"Failed to draw octagon on {fabricator.getDescription()}"


    @pytest.mark.skipif(condition=testLevelToRun < 5, reason="Not doing lvl 5 tests")
    @pytest.mark.order(5)
    def test_center(self, function_setup):
        fabricator = function_setup
        assert fabricator.device.goTo(
            Vector3(125.0, 100.0, 2.0)), f"Failed to go to center on {fabricator.getDescription()}"

    @pytest.mark.skip(reason="Pause isn't implemented yet")
    @pytest.mark.order(6)
    # @pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
    def test_pause(self, function_setup):
        fabricator = function_setup
        if not isinstance(fabricator.device, canPause):
            pytest.skip(f"{fabricator.getDescription()} doesn't support pausing")
        assert fabricator.device.pause(), f"Failed to pause on {fabricator.getDescription()}"


    @pytest.mark.skip(reason="Resume isn't implemented yet")
    @pytest.mark.order(7)
    # @pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
    def test_resume(self, function_setup):
        fabricator = function_setup
        if not isinstance(fabricator.device, canPause):
            pytest.skip(f"{fabricator.getDescription()} doesn't support resuming")
        assert fabricator.device.resume(), f"Failed to resume on {fabricator.getDescription()}"


    @pytest.mark.skip(reason="Cancel isn't implemented yet")
    @pytest.mark.order(8)
    # @pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
    def test_cancel(self, function_setup):
        fabricator = function_setup
        assert fabricator.cancel(), f"Failed to cancel on {fabricator.getDescription()}"


    @pytest.mark.skip(reason="getStatus isn't implemented yet")
    @pytest.mark.order(9)
    # @pytest.mark.skipif(condition=testLevelToRun < 10, reason="Not doing lvl 10 tests")
    def test_status(self, function_setup):
        fabricator = function_setup
        assert fabricator.getStatus() is not None, f"Failed to get status on {fabricator.getDescription()}"


    @pytest.mark.skipif(condition=testLevelToRun < 9, reason="Not doing lvl 9 tests")
    @pytest.mark.order(10)
    def test_gcode(self, function_setup):
        fabricator = function_setup
        expectedTime = 3 * 60
        file = "../server/xyz-cali-cube"
        if self.shortTest:
            file = file + "-mini"
        if isinstance(fabricator.device, Ender3):
            file = file + "_ENDER3.gcode"
            expectedTime = 4 * 60 + 15 if self.shortTest else 28 * 60
        elif isinstance(fabricator.device, PrusaMK4S):
            file = file + "_MK4S.gcode"
            expectedTime = 180 if self.shortTest else 1800
        elif isinstance(fabricator.device, PrusaMK4):
            file = file + "_MK4.gcode"
            expectedTime = 10 * 60 if self.shortTest else 1800
        # expectedTime = 2040 # for my personal home test, 1072
        expectedMinutes, expectedSeconds = divmod(expectedTime, 60)
        time = datetime.now()
        assert fabricator.device.parseGcode(file), f"Failed to parse Gcode on {fabricator.getDescription()}"
        time = datetime.now() - time
        minutes, seconds = divmod(time.seconds, 60)
        fabricator.device.serialConnection.write(b"M31\n")
        line = ""
        while not re.search(r"\d+m \d+s", line):
            line = fabricator.device.serialConnection.readline().decode("utf-8")
        printMinutes, printSeconds = map(int, re.findall(r"\d+", line))
        printTime = printMinutes * 60 + printSeconds
    
        timeBoundary = max(120, expectedTime // 5)
        assert printTime - expectedTime < timeBoundary, f"Failed to print within time boundary of expected time on {fabricator.getDescription()}. Expected: {int(expectedMinutes):02}:{int(expectedSeconds):02}, Actual: {int(printMinutes):02}:{int(printSeconds):02}"
        assert time.seconds - expectedTime < timeBoundary, f"Failed to print within time boundary of expected time on {fabricator.getDescription()}. Expected: {int(expectedMinutes):02}:{int(expectedSeconds):02}, Actual: {int(minutes):02}:{int(seconds):02}"
