import os
from datetime import datetime
import re
import pytest
from app import fabricator_list
from Classes.Jobs import Job
from parallel_test_runner import testLevel

testLevelToRun = testLevel
shortTest = True

def __desc__(): return "Fabricator Tests"
def __repr__(): return f"test_fabricator.py running on port {os.getenv('PORT')}"

def cali_cube_setup(fabricator=None):
    if fabricator is None:
        fabricator = fabricator_list.getFabricatorByPort(os.getenv("PORT"))
    file = "../server/xyz-cali-cube"
    if shortTest: file = file + "-mini"
    file = file + f"_{fabricator.device.MODEL}.gcode"
    return file

@pytest.mark.dependency(depends=["test_device.py::test_connection"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_status(app, fabricator):
    assert fabricator.getStatus() is not None, f"Failed to get status on {fabricator.getDescription()}"
    assert fabricator.device.status is not None, f"Failed to get status on device of {fabricator.getDescription()}"
    assert fabricator.getStatus() == fabricator.device.status, f"Internal status mismatch: fabricator: {fabricator.getDescription()}, device: {fabricator.device.status}"
    assert fabricator.getStatus() == "idle", f"Status incorrect at {fabricator.getDescription()}, expected idle, got {fabricator.getStatus()}"

@pytest.mark.dependency(depends=["test_device.py::test_connection"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 1, reason="Not doing lvl 1 tests")
def test_add_job(app, fabricator):
    file = cali_cube_setup(fabricator=fabricator)
    with open(file, "r") as f:
        assert fabricator.queue.addToFront(Job(f.read(), "xyz cali cube", 3, "ready", file, False, 1, fabricator.name)), f"Failed to add job on {fabricator.getDescription()}"
    for job in fabricator.queue.getQueue():
        assert job.status == "ready", f"Job status incorrect on {fabricator.getDescription()}"
    fabricator.queue.removeJob()
    assert len(fabricator.queue.getQueue()) == 0, f"Failed to remove job on {fabricator.getDescription()}"

@pytest.mark.dependency(depends=["test_device.py::test_home", "test_fabricator.py::test_add_job"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 7, reason="Not doing lvl 7 tests")
def test_pause_and_resume(app, fabricator):
    from Mixins.canPause import canPause
    if not isinstance(fabricator.device, canPause):
        pytest.skip(f"{fabricator.getDescription()} doesn't support pausing")

    def parse_gcode():
        try:
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
        except Exception as f:
            fabricator.setStatus("error")
            raise f

    def pause_and_resume_fabricator():
        try:
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
        except Exception as f:
            fabricator.setStatus("error")
            raise f

        fabricator.resetToIdle()
        assert fabricator.getStatus() == "idle", f"Failed to reset to idle on {fabricator.getDescription()}, fab status: {fabricator.getStatus()}, dev status: {fabricator.device.status}"

    assert fabricator.device.home(), f"Failed to home on {fabricator.getDescription()}"
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=2) as executor:
        parse_future = executor.submit(parse_gcode)
        pause_future = executor.submit(pause_and_resume_fabricator)

        for future in as_completed([parse_future, pause_future]):
            future.result()

@pytest.mark.dependency(depends=["test_device.py::test_home", "test_fabricator.py::test_add_job"], scope="session")
@pytest.mark.skipif(condition=testLevelToRun < 9, reason="Not doing lvl 9 tests")
def test_gcode_print_time(app, fabricator):
    isVerbose = os.getenv("LEVEL") == "DEBUG"
    from Classes.Fabricators.Printers.Printer import Printer
    if not isinstance(fabricator.device, Printer):
        pytest.skip(f"{fabricator.getDescription()} doesn't support printing gcode")
    file = cali_cube_setup(fabricator=fabricator)
    # expectedTime = 2040 # for my personal home test, 1072
    from Classes.Fabricators.Fabricator import getFileConfig
    config = getFileConfig(file)
    expectedTime = int(config["expected_time"])
    fabricator.device.changeFilament(config["filament_type"], float(config["filament_diameter"]))
    fabricator.device.changeNozzle(float(config["nozzle_diameter"]))
    expectedDays, expectedHours, expectedMinutes, expectedSeconds = 0, 0, 0, 0
    if expectedTime >= 60:
        expectedMinutes, expectedSeconds = divmod(expectedTime, 60)
    if expectedMinutes >= 60:
        expectedHours, expectedMinutes = divmod(expectedMinutes, 60)
    if expectedHours >= 24:
        expectedDays, expectedHours = divmod(expectedHours, 24)
    if isVerbose: fabricator.device.logger.debug(f"Expected print time: {expectedDays:02}:{expectedHours:02}:{expectedMinutes:02}:{expectedSeconds:02}")
    with open(file, "r") as f:
        fabricator.queue.addToFront(Job(f.read(), "xyz cali cube", fabricator.dbID, "ready", file, False, 1, fabricator.name))
        time = datetime.now()
        fabricator.begin(isVerbose=isVerbose)
    time = datetime.now() - time
    if isVerbose: fabricator.device.logger.debug(f"Actual print time: {time}")
    fabricator.device.serialConnection.write(b"M31\n")
    line = ""
    from Mixins.hasResponseCodes import checkTime
    while not checkTime(line):
        line = fabricator.device.serialConnection.readline().decode("utf-8")
    if isVerbose: fabricator.device.logger.debug(f"not stuck in print time loop: time: {line}")

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
    expectedTimeBool = (printTime - expectedTime) < timeBoundary
    measuredTimeBool = (time.seconds - expectedTime) < timeBoundary
    assert expectedTimeBool, f"Failed to print within time boundary of expected time on {fabricator.getDescription()}. Expected: {expectedString}, Actual: {printString}"
    assert measuredTimeBool, f"Failed to print within time boundary of measured time on {fabricator.getDescription()}. Expected: {expectedString}, Actual: {measuredTimeString}"