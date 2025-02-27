from Classes.Fabricators.Printers.MakerBot.MakerBotPrinter import MakerBotPrinter
from globals import PID


class Replicator2(MakerBotPrinter):
    MODEL = "Replicator 2"
    PRODUCTID = PID.REPLICATOR2
    DESCRIPTION = "Replicator 2 - CDC"

    def startupSequence(self):
        self.serialConnection.write("M73 P0 ; enable build progress")
        self.serialConnection.write("G162 X Y F3000 ; home XY maximum")
        self.serialConnection.write("G161 Z F1200 ; home Z minimum")
        self.serialConnection.write("G92 Z-5 ; set Z to -5")
        self.serialConnection.write("G1 Z0 ; move Z to 0")
        self.serialConnection.write("G161 Z F100 ; home Z slowly")
        self.serialConnection.write("M73 P0 ; enable build progress")
        self.serialConnection.write("M73 P0 ; enable build progress")
        self.serialConnection.write("M73 P0 ; enable build progress")
        self.serialConnection.write("M73 P0 ; enable build progress")
        self.serialConnection.write("M132 X Y Z A B ; recall home offsets")
        self.serialConnection.write("G1 X-145 Y-75 Z30 F9000 ; move to wait position off table")
        self.serialConnection.write("G130 X20 Y20 Z20 A20 B20 ; lower stepper Vrefs while heating")
        self.serialConnection.write("M126 S[fan_speed_pwm]")
        self.serialConnection.write("M104 S[extruder0_temperature] T0")
        self.serialConnection.write("M133 T0 ; stabilize extruder temperature")
        self.serialConnection.write("G130 X127 Y127 Z40 A127 B127 ; default stepper Vrefs")
        self.serialConnection.write("G92 A0 ; zero extruder")
        self.serialConnection.write("G1 Z0.4 ; position nozzle")
        self.serialConnection.write("G1 E25 F300 ; purge nozzle")
        self.serialConnection.write("G1 X-140 Y-70 Z0.15 F1200 ; slow wipe")
        self.serialConnection.write("G1 X-135 Y-65 Z0.5 F1200 ; lift")
        self.serialConnection.write("G92 A0 ; zero extruder")
        self.serialConnection.write("M73 P1 ;@body (notify GPX body has started)")