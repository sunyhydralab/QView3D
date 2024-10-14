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

def setupTest():
    pass

def test(printer: Fabricator):
    print(f"Testing {printer.getDescription()}")
    if printer.device.home():
        printColor(green, "Homed")
    else:
        printColor(red, "Failed to home")

    if printer.device.goTo(endLocation):
        printColor(green, "Moved to end location")
    else:
        printColor(red, "Failed to move to end location")

    printer.device.disconnect()

def teardownTest():
    pass

endLocation = Vector3(125.0,100.0,2.0)
with app.app_context():
    # home prusa mk4s
    # FabricatorList.init()
    # FabricatorList.addFabricator("COM5")
    # HomePrinter = FabricatorList.fabricators[0].setName("Home Printer")
    #test(HomePrinter)

    # nate's Ender 3 Pro
    EnderPro = Fabricator(Ports.getPortByName("COM5"), "Ender 3 Pro")
    test(EnderPro)

    # school prusa mk4
    # PrusaMK4 = Fabricator(Ports.getPortByName("COM3"), "Prusa MK4")
    # test(PrusaMK4)

    # school Ender 3
    # Ender3 = Fabricator(Ports.getPortByName("COM4"), "Ender 3")
    # test(Ender3)