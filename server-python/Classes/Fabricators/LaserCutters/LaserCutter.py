from abc import ABCMeta
from Classes.Fabricators.Device import Device

class LaserCutter(Device, metaclass=ABCMeta):
    laserPower: int | None = None
    feedRate: int | None = None
    focusHeight: float | None = None

    def changeFocusHeight(self):
        pass