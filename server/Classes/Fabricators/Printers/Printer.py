from abc import ABCMeta
from Classes.Fabricators.Device import Device

class Printer(Device, metaclass=ABCMeta):
    filamentType: str | None = None
    filamentDiameter: float | None = None
    nozzleDiameter: float | None = None
    bedTemperature: int | None = None
    nozzleTemperature: int | None = None

    def changeFilament(self):
        pass