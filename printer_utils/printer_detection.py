import serial.tools.list_ports

# Function to get a list of connected 3D prints.
def get3DPrinterList():
    # Get a list of all the connected serial ports.
    ports = serial.tools.list_ports.comports()
    # Print out the list of ports.
    for port in ports:
        # Save the port and description to list. With key value pairs of port and description.
        printerList = []
        # Keep a list of supported printers.
        supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
        # Check if the printer is supported and if true add it to the list.
        if port.description in supportedPrinters:
            printerList.append(port)   
        # Print out the list of supported printers.
        print(f"Port: {port.device}, Descp: {port.description}")
    # Return the list of supported printers.
    return printerList
    