import re
from abc import ABCMeta, abstractmethod
from Classes.Vector3 import Vector3
from services.app_service import current_app

class hasResponsecodes(metaclass=ABCMeta):
    headPosition: Vector3 = None

    @abstractmethod
    def getPrintTime(self):
        pass

    @abstractmethod
    def getToolHeadLocation(self) -> Vector3:
        pass

def checkOK(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return "ok" in line

def checkXYZ(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return ("x:" in line) and ("y:" in line) and ("z:" in line)

def checkEcho(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip().lower()
    return line.startswith("echo")

def checkBedTemp(line, dev):
    from Classes.Fabricators.Printers.Printer import Printer
    assert isinstance(dev, Printer), f"Expected Printer, got {type(dev)}"
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    try:
        match = re.search(r'B:(\d+\.?\d*) ?/?(\d+\.?\d*)?', line)
        temps = match.groups() if match else None
        return checkTemp(temps, dev, ["bedTemperature", "bedTargetTemperature"])
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkExtruderTemp(line, dev):
    from Classes.Fabricators.Printers.Printer import Printer
    assert isinstance(dev, Printer), f"Expected Printer, got {type(dev)}"
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    try:
        match = re.search(r'T:(\d+\.?\d*) ?/?(\d+\.?\d*)?', line)
        temps = match.groups() if match else None
        return checkTemp(temps, dev, ["extruderTemperature", "extruderTargetTemperature"])
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkTemp(temps, dev, attrs):
    try:
        if not temps: return False
        match len(temps):
            case 2:
                setattr(dev, attrs[0], float(temps[0]))
                setattr(dev, attrs[1], float(temps[1]))
            case 1:
                setattr(dev, attrs[0], float(temps[0]))
            case _:
                return False
        return abs(getattr(dev, attrs[1]) - getattr(dev, attrs[0])) < 0.75
    except Exception as e:
        return current_app.handle_errors_and_logging(e, dev.logger)

def checkTime(line, dev):
    line = (line.decode() if isinstance(line, bytes) else line).strip()
    return re.search(r"\d+m \d+s", line) or re.search(r"\d+ min, \d+ sec", line)