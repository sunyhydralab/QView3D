from abc import ABCMeta
from app import app
from Classes.Fabricators.Device import Device

class Printer(Device, metaclass=ABCMeta):
    filamentType: str | None = None
    filamentDiameter: float | None = None
    nozzleDiameter: float | None = None
    bedTemperature: int | None = None
    nozzleTemperature: int | None = None

    def changeFilament(self, filamentType: str, filamentDiameter: float):
        if not isinstance(filamentDiameter, float):
            filamentDiameter = float(filamentDiameter)
        try:
            if self.status is "idle":
                self.filamentType = filamentType
                self.filamentDiameter = filamentDiameter
            else:
                raise Exception("Printer is not idle")
        except Exception as e:
            if self.logger is None:
                with app.app_context():
                    app.logger.error("Error changing filament:")
                    app.logger.error(e)
            else:
                self.logger.error("Error changing filament:")
                self.logger.error(e)
        self.filamentType = filamentType
        self.filamentDiameter = filamentDiameter

    def changeNozzle(self, nozzleDiameter: float):
        if not isinstance(nozzleDiameter, float):
            nozzleDiameter = float(nozzleDiameter)
        self.nozzleDiameter = nozzleDiameter