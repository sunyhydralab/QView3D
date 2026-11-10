from Classes.Fabricators.Device import Device


class MockPrinter(Device):
    MODEL = "Mock Printer"
    DESCRIPTION = "Python Mock Printer"
    MAXFEEDRATE = 12000