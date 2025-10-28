import serial
import serial.tools.list_ports
import time

def get3DPrinterList():
    ports = serial.tools.list_ports.comports()
    printer_list = []
    for port in ports:
        printer_list.append(port)
    return printer_list

def parseGcode(path):
    with open(path, "r") as g:
        for line in g:
            line = line.strip()
            if len(line) == 0 or line.startswith(";"):
                continue
            sendGcode(line)

def sendGcode(message):
    # WARNING: 'ser' must be defined globally before calling this function
    ser.write(f"{message}\n".encode('utf-8'))
    time.sleep(0.1)
    while True:
        response = ser.readline().decode("utf-8").strip()
        if "ok" in response:
            break
    print(f"Command: {message}, Received: {response}")

def resetPrinter():
    sendGcode("G28")
    sendGcode("G92 E0")

