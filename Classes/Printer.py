import serial
import serial.tools.list_ports
import time
from Classes import Queue

# Class for each printer.
class Printer:
    # Constructor for the Printer class
    def __init__(self, serial_port, filament=None):
        self.serial_port = serial_port
        self.ser = None
        self.filament = None
        self.queue = Queue()

    # Method to connect to the printer via serial port.
    def connect(self):
        self.ser = serial.Serial(self.serial_port, 115200, timeout=1)

    # Method to disconnect from the printer via serial port.
    def disconnect(self):
        if self.ser:
            self.ser.close()

    # Method to reset the printer. Sends the printer to home and resets the extruder.
    def reset(self):
        self.sendGcode("G28")
        self.sendGcode("G92 E0")

    # Method to send gcode commands to the printer.
    def sendGcode(self, message):
        self.ser.write(f"{message}\n".encode("utf-8"))
        time.sleep(0.1)
        while True:
            response = self.ser.readline().decode("utf-8").strip()
            if "ok" in response:
                break
        print(f"Command: {message}, Received: {response}")

    # Method to print a job.
    def printJob(self, job):
        for line in job.gcode_lines:
            self.sendGcode(line)

    # Method to get a list of all the connected serial ports. Static Method that can be called without an instance.
    @staticmethod
    def getSupportedPrinters():
        # Get a list of all the connected serial ports.
        ports = serial.tools.list_ports.comports()
        # Make a list of the supported printers.
        for port in ports:
            # Save the port and description to list. With key value pairs of port and description.
            printerList = []
            # Keep a list of supported printers.
            supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
            # Check if the printer is supported and if true add it to the list.
            # if port.description in supportedPrinters:
            printerList.append(port)
            # Print out the list of supported printers.
            print(f"Port: {port.device}, Descp: {port.description}")
        # Return the list of supported printers.
        return printerList