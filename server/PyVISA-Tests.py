import re

import pyvisa
from pyvisa import constants
from pyvisa.resources.resource import Resource
from pyvisa import ResourceManager
from serial.tools.list_ports import grep
import time
from Classes.MyPyVISA.CustomResourceManager import CustomResourceManager
from Classes.MyPyVISA.CustomTCPIPInstrument import CustomTCPIPInstrument
from Classes.MyPyVISA.CustomSerialInstrument import CustomSerialInstrument


def connect_to_printer(rm: ResourceManager, resource_string: str):
    """Connects to the 3D printer using the given resource string."""
    try:
        printer: Resource = rm.open_resource(resource_string, baud_rate=115200, timeout=5000)
        printer.write_termination = '\n'
        printer.read_termination = '\n'
        return printer
    except pyvisa.VisaIOError as e:
        print(f"Error connecting to printer: {e}")
        return None


def send_command(printer, command: str):
    """Sends a command to the printer and reads the response."""
    if printer:
        printer.write(command)
        time.sleep(0.1)  # Give the printer some time to respond
        try:
            response = printer.read()
            print(f"Response: {response}")
            return response
        except pyvisa.errors.VisaIOError:
            print("No response received.")
    else:
        print("Printer is not connected.")



def main():
    rm = CustomResourceManager('@py')
    rm.register_resource_class(constants.InterfaceType.asrl, "INSTR", CustomSerialInstrument)
    rm.register_resource_class(constants.InterfaceType.tcpip, "INSTR", CustomTCPIPInstrument)
    resources = rm.list_resources()
    print(f"resources: {resources}")
    printers = []
    for resource in resources:
        if re.match(r"ASRL\d+::INSTR", resource):
            print(f"Found a printer: {resource}")
            port = re.sub(r"ASRL", "COM", re.sub(r"::INSTR", "", resource))
            pyserial_device = next((dev for dev in grep(port)), None)
            print(f"PySerial device: {pyserial_device}")
            print(f"PID: {pyserial_device.pid:04X}")
            print(f"VID: {pyserial_device.vid:04X}")
            print(f"Serial number: {pyserial_device.serial_number}")
            printers.append(rm.open_resource(resource, baud_rate=115200, timeout=5000, pid=pyserial_device.pid, vid=pyserial_device.vid, serial_number=pyserial_device.serial_number))


    connected_resources = rm.list_opened_resources()

    for resource in connected_resources:
        print(f"{resource.resource_name}")
        if hasattr(resource, "pid"):
            print(f"{resource.pid:04X}")
        if hasattr(resource, "vid"):
            print(f"{resource.vid:04X}")
        if hasattr(resource, "serial_number"):
            print(f"{resource.serial_number}")
        if hasattr(resource, "baud_rate"):
            print(f"{resource.baud_rate}")
        print(f"{resource.timeout}")
        print()

    for printer in printers:
        if printer:
            send_command(printer, "G28")
            printer.close()
            print("Connection closed.")


if __name__ == "__main__":
    main()
