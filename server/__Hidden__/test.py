import time
from datetime import datetime
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Jobs import Job
from Classes.Vector3 import Vector3
from Classes.Ports import Ports
import subprocess
import sys
import os
from flask import jsonify

red = '\033[31m'
green = '\033[32m'
yellow = '\033[33m'
blue = '\033[34m'
magenta = '\033[35m'
cyan = '\033[36m'
reset = '\033[0m'

def main():
    # Determine which printer model to instantiate
    model_id = 1  # Default to Prusa MK4

    # Get root path for proper execution
    from globals import root_path
    emu_path = os.path.abspath(os.path.join(root_path, "printeremu"))
    cmd = "./cmd/test_printer.go"
    emu_cmd = "-conn"

    # Run the Go emulator as a background process
    try:
        print("Starting emulator process")
        process = subprocess.Popen(
            ["go", "run", cmd, str(model_id), emu_cmd],
            cwd=emu_path,
        )
        print(f"Emulator process started with PID: {process.pid}")
        # while the process is running, wait for it to finish
        poll_result = process.wait()
        print("Emulator process finished with return code:", poll_result)
        return "process finished"


    except FileNotFoundError:
        print("Go command not found. Ensure Go is installed and available in PATH.")
        return "Go command not found"


def color_string(color, message):
    return color + message + reset


def test(testToRun: bool):
    if testToRun:
        return color_string(green, "Pass")
    else:
        color_string(red, "Fail")


def runTests(fabricator: Fabricator, isVerbose=False):
    # setup Tests
    tests = 0
    passes = 0
    logger = fabricator.device.logger
    logger.info(f"Testing {fabricator.getDescription()}")

    # run tests
    tests += 1
    result = test(fabricator.device is not None)
    passes += 1 if result else 0
    logger.info(f"test {tests}: Connect {result}", end=" ")


    # tests += 1
    # logger.info(f"test {tests}: Home", end=" ")
    # passes += test(fabricator.device.home(isVerbose=isVerbose))
    #
    # tests += 1
    # logger.info(f"test {tests}: Square", end=" ")
    # squarePasses = 0
    # for point in patterns[0]:
    #     squarePasses += 1 if fabricator.device.goTo(point) else 0
    # passes += test(squarePasses == len(patterns[0]))
    #
    # tests += 1
    # logger.info(f"test {tests}: Octagon", end=" ")
    # squarePasses = 0
    # for point in patterns[1]:
    #     squarePasses += 1 if fabricator.device.goTo(point) else 0
    # passes += test(squarePasses == len(patterns[1]))

    # tests += 1
    # logger.info(f"test {tests}: Center", end=" ")
    # passes += test(fabricator.device.goTo(endLocation))

    tests += 1
    expectedTime = 9 * 60 + 15
    expectedMinutes, expectedSeconds = divmod(expectedTime, 60)
    time = datetime.now()
    file = "server/gcode-examples/cali-cubes/mini/xyz-cali-cube-mini_MK4.gcode"
    with open(file, "r") as f:
        fabricator.queue.addToFront(Job(f.read(), "xyz cali cube", fabricator.dbID, "ready", file, False, 1, fabricator.name))
        fabricator.begin()
    time = datetime.now() - time
    minutes, seconds = divmod(time.seconds, 60)
    logger.info(f"\texpect print time: {int(expectedMinutes):02}:{int(expectedSeconds):02}")
    logger.info(f"\tactual print time: {int(minutes):02}:{int(seconds):02}")
    result = test(fabricator.status == "complete")
    passes += 1 if result else 0
    logger.info(f"test {tests}: Parse Gcode {result}", end=" ")

    # tests += 1
    # logger.info(f"test {tests}: Pause", end=" ")
    # passes += test(fabricator.device.pause())
    #
    # tests += 1
    # logger.info(f"test {tests}: Resume", end=" ")
    # passes += test(fabricator.device.resume())
    #
    # tests += 1
    # logger.info(f"test {tests}: Cancel", end=" ")
    # passes += test(fabricator.device.cancel())
    #
    #
    # tests += 1
    # logger.info(f"test {tests}: Status", end=" ")
    # passes += test(fabricator.device.status())

    # teardown tests
    fabricator.device.disconnect()
    if passes == tests:
        logger.info(color_string(green, f"All tests passed ({passes}/{tests})"))
    else:
        logger.info(color_string(red, f"{passes}/{tests} tests passed"))

main()
#
# endLocation = Vector3(125.0, 100.0, 2.0)
# patterns = [
#     [Vector3(50.0, 50.0, 2.0), Vector3(200.0, 50.0, 2.0), Vector3(200.0, 150.0, 2.0), Vector3(50.0, 150.0, 2.0)],
#     # square
#     [Vector3(50.0, 100.0, 2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0, 50.0, 2.0), Vector3(200.0, 100.0, 2),
#      Vector3(200.0, 150.0, 2.0), Vector3(150.0, 200.0, 2), Vector3(100.0, 200.0, 2.0), Vector3(50.0, 150.0, 2.0)],
#     # octagon
#     ]
# from app import app
# with app.app_context():
#     PrusaMK4S = None
#     PrusaMK4 = None
#     PrusaMK3 = None
#     Ender3 = None
#     MakerBot = None
#     EnderPro = None
#
#     # FabricatorList.init()
#     # for printer in FabricatorList.fabricators:
#     #     runTests(printer)
#
#     # ari's MK4S
#     if Ports.getPortByName("COM5") is not None:
#         PrusaMK4S = Fabricator(Ports.getPortByName("COM5"), "Prusa MK4S")
#
#     # nate's Ender 3 Pro
#     if Ports.getPortByName("COM6") is not None:
#         EnderPro = Fabricator(Ports.getPortByName("COM6"), "Ender 3 Pro")
#
#     # school prusa mk4
#     if Ports.getPortByName("COM3") is not None:
#         PrusaMK4 = Fabricator(Ports.getPortByName("COM3"), "Prusa MK4")
#         # PrusaMK4.device.logger.setLevel(PrusaMK4.device.logger.DEBUG)
#         # PrusaMK4.device.sendGcode(b'G29 A\n', isVerbose=True)
#
#     # school Ender 3
#     if Ports.getPortByName("COM4") is not None:
#         Ender3 = Fabricator(Ports.getPortByName("COM4"), "Ender 3")
#         # Ender3.device.sendGcode(b"M109 S50\n", isVerbose=True)
#
#     # school Makerbot
#     if Ports.getPortByName("COM7") is not None:
#         MakerBot = Fabricator(Ports.getPortByName("COM7"), "MakerBot")
#
#     # school MK3
#     if Ports.getPortByName("COM9") is not None:
#         PrusaMK3 = Fabricator(Ports.getPortByName("COM9"), "Prusa MK3")
#         # PrusaMK3.device.connect()
#         # PrusaMK3.device.logger.setLevel(PrusaMK3.device.logger.DEBUG)
#         # PrusaMK3.device.sendGcode(PrusaMK3.device.pauseCMD, isVerbose=True)
#         # time.sleep(5)
#         # PrusaMK3.device.sendGcode(PrusaMK3.device.resumeCMD, isVerbose=True)
#         # time.sleep(5)
#         # PrusaMK3.device.sendGcode(PrusaMK3.device.cancelCMD, isVerbose=True)
#         # print(PrusaMK3.device.home(isVerbose=True))
#
#     # for fab in [PrusaMK4S, PrusaMK4, PrusaMK3, Ender3, MakerBot, EnderPro]:
#     #     if fab is not None:
#     #         runTests(fab)
#
#     for fab in [PrusaMK4S, PrusaMK4, PrusaMK3, Ender3, MakerBot, EnderPro]:
#         if fab is not None and fab.device is not None and fab.device.serialConnection is not None and fab.device.serialConnection.is_open:
#             fab.device.disconnect()
