from abc import ABCMeta
from Classes.Fabricators.Device import Device

class CNCMachine(Device, metaclass=ABCMeta):
    toolDiameter: float | None = None
    toolType: str | None = None
    spindleSpeed: int | None = None
    feedRate: int | None = None
    depthOfCut: float | None = None

    def changeTool(self):
        pass