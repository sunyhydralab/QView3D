from abc import ABCMeta
from app import app
from Classes.Fabricators.Device import Device

class Printer(Device, metaclass=ABCMeta):
    bedTemperature: int | None = None
    nozzleTemperature: int | None = None

    def __init__(self, serialPort, consoleLogger=None, fileLogger=None):
        super().__init__(serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger)
        self.filamentType = None
        self.filamentDiameter = None
        self.nozzleDiameter = None

    def changeFilament(self, filamentType: str, filamentDiameter: float):
        if not isinstance(filamentDiameter, float):
            filamentDiameter = float(filamentDiameter)
        try:
            assert self.status is "idle", "Printer is not idle"
            self.filamentType = filamentType
            self.filamentDiameter = filamentDiameter
        except Exception as e:
            with app.app_context():
                app.logger.error("Error changing filament:")
                app.logger.error(e)

    def changeNozzle(self, nozzleDiameter: float):
        if not isinstance(nozzleDiameter, float):
            nozzleDiameter = float(nozzleDiameter)
        self.nozzleDiameter = nozzleDiameter