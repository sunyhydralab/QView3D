import re
from datetime import datetime
from Classes.FabricatorList import FabricatorList
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Vector3 import Vector3
from Classes.Ports import Ports
from app import app

red = '\033[31m'
green = '\033[32m'
yellow = '\033[33m'
blue = '\033[34m'
magenta = '\033[35m'
cyan = '\033[36m'
reset = '\033[0m'

def printColor(color, message):
    print(color + message + reset)
    
def test(testToRun: bool):
    if testToRun:
        printColor(green, "Pass")
        return 1
    else:
        printColor(red, "Fail")
        return 0

def runTests(fabricator: Fabricator, isVerbose=False):
    # setup Tests
    tests = 0
    passes = 0
    print(f"Testing {fabricator.getDescription()}")

    # run tests
    tests += 1
    print(f"test {tests}: Connect", end=" ")
    passes += test(fabricator.device is not None)

    # tests += 1
    # print(f"test {tests}: Home", end=" ")
    # passes += test(fabricator.device.home(isVerbose=isVerbose))
    #
    # tests += 1
    # print(f"test {tests}: Square", end=" ")
    # squarePasses = 0
    # for point in patterns[0]:
    #     squarePasses += 1 if fabricator.device.goTo(point) else 0
    # passes += test(squarePasses == len(patterns[0]))
    #
    # tests += 1
    # print(f"test {tests}: Octagon", end=" ")
    # squarePasses = 0
    # for point in patterns[1]:
    #     squarePasses += 1 if fabricator.device.goTo(point) else 0
    # passes += test(squarePasses == len(patterns[1]))

    # tests += 1
    # print(f"test {tests}: Center", end=" ")
    # passes += test(fabricator.device.goTo(endLocation))

    tests += 1
    print(f"test {tests}: Parse Gcode", end=" ")
    expectedTime = 3 * 60
    expectedMinutes, expectedSeconds = divmod(expectedTime, 60)
    time = datetime.now()
    passes += test(fabricator.device.parseGcode("server/xyz-cali-cube-mini_MK4.gcode", isVerbose=True))
    time = datetime.now() - time
    minutes, seconds = divmod(time.seconds, 60)
    print(f"\texpect print time: {int(expectedMinutes):02}:{int(expectedSeconds):02}")
    print(f"\tactual print time: {int(minutes):02}:{int(seconds):02}")

    # tests += 1
    # print(f"test {tests}: Pause", end=" ")
    # passes += test(fabricator.device.pause())
    #
    # tests += 1
    # print(f"test {tests}: Resume", end=" ")
    # passes += test(fabricator.device.resume())
    #
    # tests += 1
    # print(f"test {tests}: Cancel", end=" ")
    # passes += test(fabricator.device.cancel())
    #
    #
    # tests += 1
    # print(f"test {tests}: Status", end=" ")
    # passes += test(fabricator.device.status())

    # teardown tests
    fabricator.device.disconnect()
    if passes == tests:
        printColor(green, f"All tests passed ({passes}/{tests})")
    else:
        printColor(red, f"{passes}/{tests} tests passed")


endLocation = Vector3(125.0,100.0,2.0)
patterns = [[Vector3(50.0,50.0,2.0), Vector3(200.0,50.0,2.0), Vector3(200.0,150.0,2.0), Vector3(50.0,150.0,2.0)], #square
            [Vector3(50.0,100.0,2.0), Vector3(100.0, 50.0, 2.0), Vector3(150.0,50.0,2.0), Vector3(200.0, 100.0, 2), Vector3(200.0,150.0,2.0), Vector3(150.0, 200.0, 2), Vector3(100.0,200.0,2.0), Vector3(50.0, 150.0, 2.0)], # octagon
            ]
with app.app_context():
    PrusaMK4S = None
    PrusaMK4 = None
    Ender3 = None
    MakerBot = None
    EnderPro = None

    # FabricatorList.init()
    # for printer in FabricatorList.fabricators:
    #     runTests(printer)

    # ari's MK4S
    if Ports.getPortByName("COM5") is not None:
        PrusaMK4S = Fabricator(Ports.getPortByName("COM5"), "Prusa MK4S", addToDB=False)
        runTests(PrusaMK4S)

    # nate's Ender 3 Pro
    if Ports.getPortByName("COM6") is not None:
        EnderPro = Fabricator(Ports.getPortByName("COM6"), "Ender 3 Pro", addToDB=False)
        runTests(EnderPro)

    # school prusa mk4
    if Ports.getPortByName("COM3") is not None:
        PrusaMK4 = Fabricator(Ports.getPortByName("COM3"), "Prusa MK4", addToDB=False)
        PrusaMK4.device.serialConnection.write(b"M31\n")
        line = ""
        while True:
            try:
                line = PrusaMK4.device.serialConnection.readline().decode("utf-8")
                if re.search(r"\d+m \d+s", line):
                    printColor(green, line)
                    break
                print(line, end="")
            except KeyboardInterrupt:
                break
        min, sec = map(int, re.findall(r"\d+", line))
        printTime = min * 60 + sec
        print(f"Print time: {min:02}:{sec:02}")
        #runTests(PrusaMK4)

    # school Ender 3
    if Ports.getPortByName("COM8") is not None:
        Ender3 = Fabricator(Ports.getPortByName("COM8"), "Ender 3", addToDB=False)
        #runTests(Ender3)
        #Ender3.device.sendGcode(b"M109 S50\n", isVerbose=True)

    # school Makerbot
    if Ports.getPortByName("COM7") is not None:
        MakerBot = Fabricator(Ports.getPortByName("COM7"), "MakerBot", addToDB=False)
        runTests(MakerBot)

    if PrusaMK4 is not None and PrusaMK4.device.serialConnection.is_open:
        PrusaMK4.device.disconnect()

    if Ender3 is not None and Ender3.device.serialConnection.is_open:
        Ender3.device.disconnect()

    if MakerBot is not None and MakerBot.device.serialConnection.is_open:
        MakerBot.device.disconnect()

    if EnderPro is not None and EnderPro.device.serialConnection.is_open:
        EnderPro.device.disconnect()


