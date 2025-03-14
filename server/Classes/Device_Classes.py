from typing import Dict, Type, Tuple

from Classes.Fabricators.Printers.Prusa.PrusaMK3 import PrusaMK3
from Classes.Fabricators.Printers.Prusa.PrusaMK4 import PrusaMK4
from Classes.Fabricators.Printers.Prusa.PrusaMK4S import PrusaMK4S
from Classes.Fabricators.Printers.Creality.Creality_Factory import Creality_Factory
from Classes.Fabricators.Printers.MakerBot.Replicator2 import Replicator2
from Classes.Fabricators.Device import Device
from globals import VID, PID

device_classes: Dict[Tuple[int, int], Type["Device"]] = {
    (VID.PRUSA.value, PID.MK3.value): PrusaMK3,
    (VID.PRUSA.value, PID.MK4.value): PrusaMK4,
    (VID.PRUSA.value, PID.MK4S.value): PrusaMK4S,
    (VID.CREALITY.value, PID.ENDER3.value): Creality_Factory,
    (VID.MAKERBOT.value, PID.REPLICATOR2.value): Replicator2
}
