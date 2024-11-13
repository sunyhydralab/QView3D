import os
import sys
from datetime import datetime
import re
import pytest
from Classes.Jobs import Job
from Classes.Fabricators.Fabricator import Fabricator
from parallel_test_runner import testLevel

testLevelToRun = testLevel
shortTest = True
fabricator = Fabricator(None, "Test Printer", addToDB=False, consoleLogger=sys.stdout)

def __desc__(): return "Fabricator Tests"
def __repr__(): return f"test_fabricator.py running on port {os.getenv('PORT')}"

def cali_cube_setup():
    file = "../server/xyz-cali-cube"
    from Classes.Fabricators.Printers.Ender.Ender3 import Ender3
    from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
    from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
    if shortTest:
        file = file + "-mini"
    if isinstance(fabricator.device, Ender3):
        file = file + "_ENDER3.gcode"
    elif isinstance(fabricator.device, PrusaMK4S):
        file = file + "_MK4S.gcode"
    elif isinstance(fabricator.device, PrusaMK4):
        file = file + "_MK4.gcode"
    return file

def fabricator_setup(port):
    if not port: return None
    from Classes.Ports import Ports
    return Fabricator(Ports.getPortByName(port), "Test Printer", addToDB=False, consoleLogger=sys.stdout)

@pytest.fixture(scope="module", autouse=True)
def function_setup(request):
    global fabricator
    fabricator = fabricator_setup(request.session.config.port)
    if fabricator is None:
        pytest.skip("No port specified")
    yield
    fabricator.device.disconnect()
    fabricator = None

@pytest.mark.dependency(depends=["test_device.py::test_connection"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_status():
    assert fabricator.getStatus() is not None, f"Failed to get status on {fabricator.getDescription()}"
    assert fabricator.device.status is not None, f"Failed to get status on device of {fabricator.getDescription()}"
    assert fabricator.getStatus() == fabricator.device.status, f"Internal status mismatch: fabricator: {fabricator.getDescription()}, device: {fabricator.device.status}"
    assert fabricator.getStatus() == "idle", f"Status incorrect at {fabricator.getDescription()}, expected idle, got {fabricator.getStatus()}"

@pytest.mark.dependency(depends=["test_device.py::test_connection"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_add_job():
    file = cali_cube_setup()
    with open(file, "r") as f:
        assert fabricator.queue.addToFront(
            Job(f.read(), "xyz cali cube", 3, "ready", file, False, 1, fabricator.name),
            3), f"Failed to add job on {fabricator.getDescription()}"
    for job in fabricator.queue.getQueue():
        assert job.status == "ready", f"Job status incorrect on {fabricator.getDescription()}"
    fabricator.queue.removeJob()
    assert len(fabricator.queue.getQueue()) == 0, f"Failed to remove job on {fabricator.getDescription()}"

@pytest.mark.dependency(depends=["test_device.py::test_home", "test_fabricator.py::test_add_job"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 7, reason="Not doing lvl 7 tests")
def test_pause_and_resume():
    from Mixins.canPause import canPause
    if not isinstance(fabricator.device, canPause):
        pytest.skip(f"{fabricator.getDescription()} doesn't support pausing")

    def parse_gcode():
        file = "../server/pauseAndResumeTest.gcode"
        from Classes.Fabricators.Fabricator import getFileConfig
        config = getFileConfig(file)
        from Classes.Fabricators.Printers.Printer import Printer
        if isinstance(fabricator.device, Printer):
            assert config["filament_type"] is not None, "Failed to get filament_type from {file}"
            assert config["filament_diameter"] is not None, f"Failed to get filament_diameter from {file}"
            assert config["nozzle_diameter"] is not None, f"Failed to get nozzle_diameter from {file}"
            fabricator.device.changeFilament(config["filament_type"], float(config["filament_diameter"]))
            fabricator.device.changeNozzle(float(config["nozzle_diameter"]))
        with open(file, "r") as f:
            job = Job(f.read(), "pauseAndResumeTest", fabricator.dbID, "ready", file, False, 1, fabricator.name)
        fabricator.queue.addToFront(job)
        result = fabricator.begin()
        import traceback
        assert not isinstance(result, Exception), f"Failed to begin on {fabricator.getDescription()}: {result}:\n{''.join(traceback.format_exception(None, result, result.__traceback__))}"
        assert fabricator.getStatus() == fabricator.device.status == "cancelled", f"Failed to cancel on {fabricator.getDescription()}, expected cancel, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
        assert fabricator.job is None, f"Failed to complete on {fabricator.getDescription()}, expected job to be None, got {fabricator.job}"

    def pause_and_resume_fabricator():
        from time import sleep
        while fabricator.getStatus() != "printing":
            assert fabricator.getStatus() != "error", f"Failed to print on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
            sleep(1)
        assert fabricator.pause(), f"Failed to pause on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
        sleep(30)
        assert fabricator.resume(), f"Failed to resume on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
        sleep(1)
        assert fabricator.cancel(), f"Failed to cancel on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
        assert fabricator.getStatus() == "cancelled", f"Failed to cancel on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"
        sleep(10)

        fabricator.resetToIdle()
        assert fabricator.getStatus() == "idle", f"Failed to reset to idle on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"

    assert fabricator.device.home(), f"Failed to home on {fabricator.getDescription()}"
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=2) as executor:
        parse_future = executor.submit(parse_gcode)
        pause_future = executor.submit(pause_and_resume_fabricator)

        for future in as_completed([parse_future, pause_future]):
            try:
                future.result()
            except Exception as e:
                raise e

@pytest.mark.dependency(depends=["test_device.py::test_home", "test_fabricator.py::test_add_job"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 9, reason="Not doing lvl 9 tests")
def test_gcode_print_time():
    from Classes.Fabricators.Printers.Printer import Printer
    if not isinstance(fabricator.device, Printer):
        pytest.skip(f"{fabricator.getDescription()} doesn't support printing gcode")
    file = cali_cube_setup()
    # expectedTime = 2040 # for my personal home test, 1072
    from Classes.Fabricators.Fabricator import getFileConfig
    config = getFileConfig(file)
    expectedTime = int(config["estimated_time"])
    fabricator.device.changeFilament(config["filament_type"], float(config["filament_diameter"]))
    fabricator.device.changeNozzle(float(config["nozzle_diameter"]))
    expectedDays, expectedHours, expectedMinutes, expectedSeconds = 0, 0, 0, 0
    if expectedTime >= 86400:
        expectedDays, expectedTime = divmod(expectedTime, 86400)
    if expectedTime >= 3600:
        expectedHours, expectedTime = divmod(expectedTime, 3600)
    if expectedTime >= 60:
        expectedMinutes, expectedTime = divmod(expectedTime, 60)
    time = datetime.now()
    with open(file, "r") as f:
        fabricator.queue.addToFront(Job(f.read(), "xyz cali cube", fabricator.dbID, "ready", file, False, 1, fabricator.name))
        time = datetime.now()
        fabricator.begin()
    time = datetime.now() - time
    fabricator.device.serialConnection.write(b"M31\n")
    line = ""
    while not re.search(r"\d+m \d+s", line):
        line = fabricator.device.serialConnection.readline().decode("utf-8")
    minutes, seconds = divmod(time.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    measuredTimeList = []
    if days > 0:
        measuredTimeList.append(f"{days:02}")
        measuredTimeList.append(f"{hours:02}")
        measuredTimeList.append(f"{minutes:02}")
        measuredTimeList.append(f"{seconds:02}")
    elif hours > 0:
        measuredTimeList.append(f"{hours:02}")
        measuredTimeList.append(f"{minutes:02}")
        measuredTimeList.append(f"{seconds:02}")
    elif minutes > 0:
        measuredTimeList.append(f"{minutes:02}")
        measuredTimeList.append(f"{seconds:02}")
    else:
        measuredTimeList.append(f"{seconds:02}")
    measuredTimeString = ":".join(measuredTimeList)

    actualTimeList = re.findall(r"\d+", line)
    printDays, printHours, printMinutes, printSeconds = 0, 0, 0, 0
    if len(actualTimeList) == 1:
        printSeconds = int(actualTimeList[0])
    elif len(actualTimeList) == 2:
        printMinutes, printSeconds = map(int, actualTimeList)
    elif len(actualTimeList) == 3:
        printHours, printMinutes, printSeconds = map(int, actualTimeList)
    elif len(actualTimeList) == 4:
        printDays, printHours, printMinutes, printSeconds = map(int, actualTimeList)
    printTime = printDays * 86400 + printHours * 3600 + printMinutes * 60 + printSeconds
    printList = []
    if printDays > 0:
        printList.append(f"{printDays:02}")
        printList.append(f"{printHours:02}")
        printList.append(f"{printMinutes:02}")
        printList.append(f"{printSeconds:02}")
    elif printHours > 0:
        printList.append(f"{printHours:02}")
        printList.append(f"{printMinutes:02}")
        printList.append(f"{printSeconds:02}")
    elif printMinutes > 0:
        printList.append(f"{printMinutes:02}")
        printList.append(f"{printSeconds:02}")
    else:
        printList.append(f"{printSeconds:02}")
    printString = ":".join(map(str, printList))
    expectedList = []
    if expectedDays > 0:
        expectedList.append(f"{expectedDays:02}")
        expectedList.append(f"{expectedHours:02}")
        expectedList.append(f"{expectedMinutes:02}")
        expectedList.append(f"{expectedSeconds:02}")
    elif expectedHours > 0:
        expectedList.append(f"{expectedHours:02}")
        expectedList.append(f"{expectedMinutes:02}")
        expectedList.append(f"{expectedSeconds:02}")
    elif expectedMinutes > 0:
        expectedList.append(f"{expectedMinutes:02}")
        expectedList.append(f"{expectedSeconds:02}")
    else:
        expectedList.append(f"{expectedSeconds:02}")
    expectedString = ":".join(map(str, expectedList))

    timeBoundary = 120
    assert printTime - expectedTime < timeBoundary, f"Failed to print within time boundary of expected time on {fabricator.getDescription()}. Expected: {expectedString}, Actual: {printString}"
    assert time.seconds - expectedTime < timeBoundary, f"Failed to print within time boundary of measured time on {fabricator.getDescription()}. Expected: {expectedString}, Actual: {measuredTimeString}"