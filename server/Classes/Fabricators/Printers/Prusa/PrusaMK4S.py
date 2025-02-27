from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
from globals import PID

class PrusaMK4S(PrusaMK4):
    MODEL = "MK4S"
    PRODUCTID = PID.MK4S
    DESCRIPTION = "Original Prusa MK4S - CDC"
    MAXFEEDRATE = 36000