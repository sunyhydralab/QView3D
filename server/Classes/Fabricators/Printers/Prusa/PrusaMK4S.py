from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4

class PrusaMK4S(PrusaMK4):
    MODEL = "MK4S"
    PRODUCTID = 0x001A
    DESCRIPTION = "Original Prusa MK4S - CDC"
    MAXFEEDRATE = 36000
    cancelCMD = b"M410"
