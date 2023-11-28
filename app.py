from flask import Flask
from routes.display import display_bp
from tasks.main import main
from Classes import serialCommunication
from Classes.PrinterList import PrinterList
from pymongo import MongoClient
import serial
import serial.tools.list_ports

app = Flask(__name__)

# start database connection
client = MongoClient('localhost')

db = client.hvamc # creates hvamc database 
printers = db.printers # creates printer collection 
universalqueue = db.bigqueue
printerObjects = None 

# Register the display_bp Blueprint
app.register_blueprint(display_bp)
app.register_blueprint(main)
    
with app.app_context(): # initialization code: Creates list of printers and adds them to DB 
    connectedPrinters = serialCommunication.get3DPrinterList() # get list of serial ports. ADD CODE TO FILTER FOR ONLY 3D PRINTERS
    # add all serial ports to DB
    for machine in connectedPrinters: 
        existing_printer = printers.find_one({'port': machine.device}) 
        if not existing_printer: # only insert if port isnt in DB 
            printer = {
                'port': machine.device, # port 
                'name': machine.description, # name of device (ex. prusa, makerbot, etc.)
                'queue': [], # printer queue 
                'state': 'ready' # get information if printer is ready from sending GCode command. 
            }
            result = printers.insert_one(printer)
            print(f"Inserted document with _id: {result.inserted_id}")
        else:
            print(f"Document with port {machine} already exists.")
        
        # loop through DB and add to printerObjects - CACHED, CLIENT-SIDE PRINTER DATA 
        printerObjects = PrinterList() # Create a list of printer objects (cached data)
        cursor = printers.find()
        for doc in cursor: 
            printerObjects.addPrinter(doc['port'], doc['_id'])
        
    print("OBJECTS: ", printerObjects.getList())

if __name__ == "__main__":
    app.run(port=8000, debug=True)
    
