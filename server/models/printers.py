from models.db import db 
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify 
from Classes.Queue import Queue
import serial
import serial.tools.list_ports
import time

# model for Printer table 
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    status = 'ready'
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) 
    queue = Queue()
    
    def __init__(self, device, description, hwid, name, status):
        self.device = device
        self.description = description 
        self.hwid = hwid 
        self.name = name 
        self.status = status
    
    # general classes 
    @classmethod
    def searchByDevice(cls, device): 
        try:
            # Query the database to find a printer by device
            printer = cls.query.filter_by(device=device).first()
            return printer is not None
        
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None
        
    @classmethod    
    def create_printer(cls, device, description, hwid, name, status): 
        printerExists = cls.searchByDevice(device)
        if printerExists: 
            return {"success": False, "message": "Printer already registered."}
        else: 
            try: 
                printer = cls(device=device, description=description, hwid=hwid, name=name, status=status)
                db.session.add(printer)
                db.session.commit()
                return {"success": True, "message": "Printer successfully registered."}
            except SQLAlchemyError as e:
                print(f"Database error: {e}")
                return jsonify({"error": "Failed to register printer. Database error"}), 500

    @classmethod 
    def get_registered_printers(cls): 
        try:
            # Query the database to get all registered printers
            printers = cls.query.all()

            # Convert the list of printers to a list of dictionaries
            printers_data = [{"device": printer.device,
                              "description": printer.description,
                              "hwid": printer.hwid,
                              "name": printer.name,
                              "status": printer.status,
                              "date": printer.date} for printer in printers]

            # Return the list of printer information in JSON format
            return jsonify({"printers": printers_data}), 200

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to retrieve printers. Database error"}), 500
       
    # printer-specific classes   
    def getDevice(self):
        return self.device
    
    def getQueue(self): 
        return self.queue
    
    def getStatus(self):
        return self.status 
    
    def connect(self):
        self.ser = serial.Serial(self.device, 115200, timeout=1)

    def disconnect(self):
        if self.ser:
            self.ser.close()

    def reset(self):
        self.send_gcode("G28")
        self.send_gcode("G92 E0")

    def send_gcode(self, message):
        self.ser.write(f"{message}\n".encode('utf-8'))
        time.sleep(0.1)
        while True:
            response = self.ser.readline().decode("utf-8").strip()
            if "ok" in response:
                break
        print(f"Command: {message}, Received: {response}")

    def print_job(self, job):
        for line in job.gcode_lines:
            self.send_gcode(line)
    
    
            
             

