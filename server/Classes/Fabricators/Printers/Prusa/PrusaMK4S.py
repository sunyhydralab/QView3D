from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4

class PrusaMK4S(PrusaMK4):
    MODEL = "Prusa MK4S"
    PRODUCTID = 0x001A
    DESCRIPTION = "Original Prusa MK4S - CDC"
    MAXFEEDRATE = 36000
