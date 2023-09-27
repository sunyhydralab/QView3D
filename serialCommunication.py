import serial
import serial.tools.list_ports
import time

# Function to get a list of connected 3D prints.
def get3DPrinterList():
    # Get a list of all the connected serial ports.
    ports = serial.tools.list_ports.comports()
    # Print out the list of ports.
    for port in ports:
        # Save the port and description to list.
        portList = []
        # Keep a list of supported printers.
        supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
        # Check if the printer is supported and if true add it to the list.
        if port.description in supportedPrinters:
            portList.append(port.device)
        # Print out the list of supported printers.
        print(f"Port: {port.device}, Descp: {port.description}")

# Function to parse the gcode file.
def parseGcode(path):
    with open(path, "r") as g:
        # Replace file with the path to the file. "r" means read mode. 
        for line in g:
            #remove whitespace
            line = line.strip() 
            # Don't send empty lines and comments. ";" is a comment in gcode.
            if len(line) == 0 or line.startswith(";"): 
                continue
            # Send the line to the printer.
            sendGcode(line)

# Function to send gcode commands
def sendGcode(message):
    # Run the get3DPrinterList and Charlie's queue function here to get the serial port of the printer.
    serialPort = "Whatever the serial port is."
    # Select the serial port. 
    ser = serial.Serial(serialPort, 115200, timeout=1)
    # Encode and send the message to the printer. 
    ser.write(f"{message}\n".encode('utf-8'))
    # Sleep the printer to give it enough time to get the instuction. 
    time.sleep(0.1)
    # Save and print out the response from the printer. We can use this for error handling and status updates.
    while True:
        response = ser.readline().decode("utf-8").strip()
        if "ok" in response:
            break
    print(f"Command: {message}, Recieved: {response}")

# Function to reset the printer.
def resetPrinter():
    # Return to home 
    sendGcode("G28")
    # Reset Extruder
    sendGcode("G92 E0")

# Close the serial port connection.

# Basic structure to send a Gcode file.  I'll add class integration later.  Just wanted to get the basic structure down. 
resetPrinter()
parseGcode("/test.gcode")
resetPrinter()

# Close the serial connection.
ser.close()

