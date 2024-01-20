from flask import Flask, jsonify 
from flask_cors import CORS 
import os 
# from Classes import serialCommunication
# from Classes.PrinterList import PrinterList 

# from pymongo import MongoClient # Importing database client 

# IMPORTING SERIAL FUNCTIONS 
# import serial
# import serial.tools.list_ports

# IMPORTING BLUEPRINTS 
from controllers.display import display_bp
# from server.main import main

# Basic app setup 
app = Flask(__name__)
app.config.from_object(__name__) # update application instantly 

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


@app.route('/shark', methods=['GET'])
def shark():
    return "This is a good shark!"

# start database connection
# client = MongoClient('localhost')

# db = client.hvamc # creates hvamc database 
# printers = db.printers # creates printer collection 
# universalqueue = db.bigqueue

# printerObjects = None # Will store list of printers. Idea is to have printer information stored in the database, but also cached in the frontend.  

# # Register the display_bp Blueprint
app.register_blueprint(display_bp)
# app.register_blueprint(main)
    
# with app.app_context(): # initialization code: Creates list of printers and adds them to DB 
#     connectedPrinters = serialCommunication.get3DPrinterList() # get list of serial ports. ADD CODE TO FILTER FOR ONLY 3D PRINTERS
#     # add all serial ports to DB
#     for machine in connectedPrinters: 
#         existing_printer = printers.find_one({'port': machine.device}) 
#         if not existing_printer: # only insert if port isnt in DB 
#             printer = {
#                 'port': machine.device, # port 
#                 'description': machine.description, # name of device (ex. prusa, makerbot, etc.)
#                 'name': 'default',
#                 'queue': [], # printer queue 
#                 'state': 'ready' # get information if printer is ready from sending GCode command. 
#             }
#             result = printers.insert_one(printer)
#             print(f"Inserted document with _id: {result.inserted_id}")
#         else:
#             print(f"Document with port {machine} already exists.")
        
#         # loop through DB and add to printerObjects - CACHED, CLIENT-SIDE PRINTER DATA 
#         printerObjects = PrinterList() # Create a list of printer objects (cached data)
#         cursor = printers.find()
#         for doc in cursor: 
#             printerObjects.addPrinter(doc['port'], doc['_id'])
        
    # print("OBJECTS: ", printerObjects.getList())

if __name__ == "__main__":
    # use threading here to constantly loop through printer objects and send stuff from queue. 
    # Also use threading to listen for GCode commands and change statuses of printer objects. 
    # Change status of printer in mongodb and also in-memory. 

    # If hits last line in GCode file: 
        # query for status ("done printing"), update. Use frontend to update status to "ready" once user removes print from plate. 
        # Before sending to printer, query for status. If error, throw error. 
    app.run(port=8000, debug=True)
    
