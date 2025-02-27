from Classes.Fabricators.Printers.Creality.CrealityPrinter import EnderPrinter
from globals import PID

class Ender3(EnderPrinter):
    MODEL = "Ender3"
    PRODUCTID = PID.ENDER3
    DESCRIPTION = "Ender 3 - CDC"
    MAXFEEDRATE = 12000


