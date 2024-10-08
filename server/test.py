import serial.tools.list_ports
from Classes.Vector3 import Vector3

homeLocation = Vector3(14.0,-4.0,2.0)

printer = serial.Serial("ttyACM0", 115200, timeout=10)
printer.write("G28\n".encode("utf-8"))
printer.write("M114\n".encode("utf-8"))
while True:
    line = printer.readline()
    try:
        print(line)
        if homeLocation.__repr__() in line.decode("utf-8"):
            break
    except KeyboardInterrupt:
        break
printer.write("M84\n".encode("utf-8"))
printer.close()