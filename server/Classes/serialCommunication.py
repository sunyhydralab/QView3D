import serial
import serial.tools.list_ports
import time

    # Function to get a list of connected 3D prints.
def get3DPrinterList():
    # Get a list of all the connected serial ports.
    ports = serial.tools.list_ports.comports()
    # print(ports)
    # Print out the list of ports.
    # Save the port and description to list. With key value pairs of port and description.
    printerList = []
    for port in ports:
        # Keep a list of supported printers.
        supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"] 
        
        # Check if the printer is supported and if true add it to the list.
        # if port.description in supportedPrinters:
        printerList.append(port)   

        
        # Print out the list of supported printers.
        # print(f"Port: {port.device}, Descp: {port.description}")
    # Return the list of supported printers.
    return printerList

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
    # Encode and send the message to the printer. 
    ser.write(f"{message}".encode('utf-8'))
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

#####################################################################################################################

# Basic structure to send a Gcode file.  I'll add class integration later.  Just wanted to get the basic structure down. 

# Reset the printer.
# resetPrinter()

# Run the get3DPrinterList and Charlie's queue function here to get the serial port of the printer.
# availablePrinters = get3DPrinterList()
# Run Charlie's queue function here to get the serial port of the printer.
# serialPort = "/dev/ttyACM0"
# # # Select the serial port. 

# ser = serial.Serial(serialPort, 115200, timeout=1)

# # Send the path to the gcode file for printing. 
# parseGcode("/test.gcode")
# # # Reset the printer.
# resetPrinter()
# # Close the serial port connection.
# ser.close()

