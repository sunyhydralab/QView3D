from models.db import db
from datetime import datetime, timezone
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, current_app
from Classes.Queue import Queue
import serial
import serial.tools.list_ports
import time
from tzlocal import get_localzone
import os 
import json 
import requests 
from dotenv import load_dotenv
load_dotenv()

# model for Printer table
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)
    queue = None
    ser = None
    status = None  # default setting on printer start. Runs initialization and status switches to "ready" automatically.
    # stopPrint = False
    responseCount = 0 # if count == 10 & no response, set error 

    def __init__(self, device, description, hwid, name, status=status, id=None):
        self.device = device
        self.description = description
        self.hwid = hwid
        self.name = name
        self.status = status
        self.date = datetime.now(get_localzone())
        self.queue = Queue()
        self.stopPrint = False 
        if id is not None:
            self.id = id
        self.responseCount = 0

    # general classes
    @classmethod
    def searchByDevice(cls, hwid):
        try:
            # Query the database to find a printer by device
            printer = cls.query.filter_by(hwid=hwid).first()
            return printer is not None

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @classmethod
    def create_printer(cls, device, description, hwid, name, status):
        printerExists = cls.searchByDevice(hwid)
        # if printerExists:
        #     return {"success": False, "message": "Printer already registered."}
        # else:
        try:
            printer = cls(
                device=device,
                description=description,
                hwid=hwid,
                name=name,
                status=status,
            )
            db.session.add(printer)
            db.session.commit()
            return {"success": True, "message": "Printer successfully registered.", "printer_id": printer.id}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to register printer. Database error"}),
                500,
            )

    @classmethod
    def get_registered_printers(cls):
        try:
            # Query the database to get all registered printers
            printers = cls.query.all()

            # Convert the list of printers to a list of dictionaries
            printers_data = [
                {   
                    "id": printer.id,
                    "device": printer.device,
                    "description": printer.description,
                    "hwid": printer.hwid,
                    "name": printer.name,
                    "status": printer.status,
                    "date": f"{printer.date.strftime('%a, %d %b %Y %H:%M:%S')} {get_localzone().tzname(printer.date)}",  # Include timezone abbreviation
                }
                for printer in printers
            ]
            # Return the list of printer information in JSON format
            return jsonify({"printers": printers_data}), 200

        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to retrieve printers. Database error"}),
                500,
            )

    @classmethod
    def getConnectedPorts(cls): 
        ports = serial.tools.list_ports.comports()
        printerList = []
        for port in ports:
            port_info = {
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid,
            }
            supportedPrinters = ["Original Prusa i3 MK3", "Makerbot"]
            # if port.description in supportedPrinters:
            printerList.append(port_info)
        return printerList
    
    @classmethod 
    def findPrinter(cls, id):
        try:
            printer = cls.query.get(id)
            return printer
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to retrieve printer. Database error"}),
                500,
            )

    def connect(self):
        self.ser = serial.Serial(self.device, 115200, timeout=1)

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.setSer(None)

    def reset(self):
        self.sendGcode("G28")
        self.sendGcode("G92 E0") 

    # Function to send gcode commands
    def sendGcode(self, message):
        try: 
            # Encode and send the message to the printer.
            self.ser.write(f"{message}\n".encode("utf-8"))
            # Sleep the printer to give it enough time to get the instruction.
            #time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()
                # if response == "":
                #     self.responseCount+=1 
                #     if(self.responseCount>=10):
                #         raise TimeoutError("No response from printer") 
                stat = self.getStatus()
                if stat == "complete":
                    break 
                if "ok" in response:
                    break
                print(f"Command: {message}, Received: {response}")
        except Exception as e: 
            # self.setStatus("error")
            print(e)
            return "error" 
        
    def gcodeEnding(self, message):
        try: 
            # Encode and send the message to the printer.
            self.ser.write(f"{message}\n".encode("utf-8"))
            # Sleep the printer to give it enough time to get the instruction.
            #time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()
                # if response == "":
                #     self.responseCount+=1 
                #     if(self.responseCount>=10):
                #         raise TimeoutError("No response from printer") 
                stat = self.getStatus()
                # print(stat)
                # if stat != "complete":
                #     break 
                if "ok" in response:
                    break
                print(f"Command: {message}, Received: {response}")
        except Exception as e: 
            # self.setStatus("error")
            print(e)
            return "error" 
        
    def parseGcode(self, path, job):
        try: 
            with open(path, "r") as g:
                # Read the file and store the lines in a list
                lines = g.readlines()
                # Only send the lines that are not empty and don't start with ";"
                # so we can correctly get the progress
                command_lines = [line for line in lines if line.strip() and not line.startswith(";")]
                # store the total to find the percentage later on
                total_lines = len(command_lines)
                # set the sent lines to 0
                sent_lines = 0
                
                # Replace file with the path to the file. "r" means read mode. 
                # now instead of reading from 'g', we are reading line by line
                for line in lines:
                    #remove whitespace
                    line = line.strip() 
                    # Don't send empty lines and comments. ";" is a comment in gcode.
                    if ";" in line:  # Remove inline comments
                        line = line.split(";")[0].strip()  # Remove comments starting with ";"
                    if len(line) == 0 or line.startswith(";"): 
                        continue
                    # Send the line to the printer.
                    
                    res = self.sendGcode(line)
                    
                    # Increment the sent lines
                    sent_lines += 1
                    # Calculate the progress
                    progress = (sent_lines / total_lines) * 100
                    
                    # Call the setProgress method
                    job.setProgress(progress)
                    
                    if res == "error": 
                        return "error"
                    
                    if self.getStatus() =="complete":
                        # self.endingSequence()
                        return "cancelled"
            return "complete"
        except Exception as e: 
            # self.setStatus("error")
            print(e)
            return "error" 
      
    # Function to send "ending" gcode commands   
    def endingSequence(self):
        self.gcodeEnding("G91")
        self.gcodeEnding("G1 F1800 E-3")
        self.gcodeEnding("G1 F3000 Z10")
        self.gcodeEnding("G90")
        self.gcodeEnding("G1 X0 Y220")
        self.gcodeEnding("M106 S0")
        self.gcodeEnding("M104 S0")
        self.gcodeEnding("M140 S0")

    def printNextInQueue(self):
        self.connect()
        job = self.getQueue().getNext() # get next job 
        try:
            if self.getSer():
                job.saveToFolder()
                path = job.generatePath()
                
                self.setStatus("printing") # set printer status to printing
                self.sendStatusToJob(job, job.id, "printing")
                # self.reset()
                # now we pass the job to the parseGcode function, so we can find that jobs progress
                verdict = self.parseGcode(path, job) # passes file to code. returns "complete" if successful, "error" if not.
                # self.endingSequence()
                if verdict =="complete":
                    self.setStatus("complete")
                    self.sendStatusToJob(job, job.id, "complete")
                elif verdict=="error": 
                    # self.endingSequence()
                    self.sendStatusToJob(job, job.id, "error")
                    self.setStatus("error")
                elif verdict=="cancelled":
                    self.endingSequence()
                    self.sendStatusToJob(job, job.id, "cancelled")
                    # self.endingSequence()
                    
                self.disconnect()
                job.removeFileFromPath(path) # remove file from folder after job complete
            # WHEN THE USER CLEARS THE JOB: remove job from queue, set printer status to ready. 
            
            else:
                self.setStatus("error")
                self.sendStatusToJob(job, job.id, "error")
            return     
        except Exception as e:
            self.setStatus("error")
            job.setStatus("error")
            return "error" 

    def fileExistsInPath(self, path): 
        if os.path.exists(path):
            return True
        
    # printer-specific classes
    def getDevice(self):
        return self.device

    def getQueue(self):
        return self.queue

    def getStatus(self):
        return self.status

    def getName(self):
        return self.name

    def getSer(self):
        return self.ser
    
    def getId(self):
        return self.id
    
    def getStopPrint(self):
        return self.stopPrint
    
    def setSer(self, port):
        self.ser = port

    #  now when we set the status, we can emit the status to the frontend
    def setStatus(self, newStatus):
        try:
            self.status = newStatus
            # Emit a 'status_update' event with the new status
            current_app.socketio.emit('status_update', {'printer_id': self.id, 'status': newStatus})
        except Exception as e:
            print('Error setting status:', e)
        
    def setStopPrint(self, stopPrint):
        self.stopPrint = stopPrint
        
    def sendStatusToJob(self, job, job_id, status):
        try:
            job.setStatus(status)
            data = {
                "printerid": self.id,
                "jobid": job_id,
                "status": status  # Assuming status is accessible here
            }
            base_url = os.getenv("BASE_URL", "http://localhost:8000")

            response = requests.post(f"{base_url}/updatejobstatus", json=data)
            if response.status_code == 200:
                print("Status sent successfully")
            else:
                print("Failed to send status:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send status to job: {e}")