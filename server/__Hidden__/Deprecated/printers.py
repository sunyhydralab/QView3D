import logging
import re
from models.db import db
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify, current_app
from Classes.Queue import Queue
import serial
import serial.tools.list_ports
import time
from datetime import datetime, timezone
from tzlocal import get_localzone
import os
import requests
from dotenv import load_dotenv
from models.config import Config
from Classes.Jobs import Job

load_dotenv()
# model for Printer table
class Printer(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc).astimezone(),
        nullable=False,
    )
    queue = None
    ser = None
    # default setting on printer start. Runs initialization and status switches to "ready" automatically.
    status = None
    # stopPrint = False
    responseCount = 0  # if count == 10 & no response, set error
    error: Exception | None = None
    extruder_temp = 0
    bed_temp = 0
    canPause = 0
    prevMes = ""
    colorbuff = 0
    terminated = 0
    emulated = False

    def __init__(self, device, description, hwid, name, status=status, id=None):
        self.device = device
        self.description = description
        self.hwid = hwid
        self.name = name
        self.status = status
        self.date = datetime.now(get_localzone())
        self.queue = Queue()
        self.stopPrint = False
        self.error = None
        self.extruder_temp = 0
        self.bed_temp = 0
        self.canPause = 0
        self.prevMes=""
        self.colorbuff=0
        self.terminated = 0
        # self.colorChangeBuffer=0

        if id is not None:
            self.id = id
        self.responseCount = 0
        
        if hwid.beginsWith("EMU"):
            self.emulated = True

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
    def getPrinterByHwid(cls, hwid):
        try:
            # Query the database to find a printer by device
            printer = cls.query.filter_by(hwid=hwid).first()
            if printer:
                return printer
            else:
                return None
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None

    @classmethod
    def create_printer(cls, device, description, hwid, name, status):
        try:
            # hwid_parts = hwid.split('-')  # Replace '-' with the actual separator
            # hwid_without_location = '-'.join(hwid_parts[:-1])

            printerExists = cls.searchByDevice(hwid)
            if printerExists:
                printer = cls.query.filter_by(hwid=hwid).first()
                return {
                    "success": False,
                    "message": "Printer already registered.",
                }
            else:
                # hwid_parts = hwid.split('-')  # Replace '-' with the actual separator
                # hwid_without_location = '-'.join(hwid_parts[:-1])

                printer = cls(
                    device=device,
                    description=description,
                    hwid=hwid,
                    name=name,
                    status=status,
                    # date = datetime.now(get_localzone())
                )
                db.session.add(printer)
                db.session.commit()
                return {
                    "success": True,
                    "message": "Printer successfully registered.",
                    "printer_id": printer.id,
                }
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"success": False, "error": "Failed to register printer. Database error"}),
                500
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
                    # Include timezone abbreviation
                    "date": f"{printer.date.strftime('%a, %d %b %Y %H:%M:%S')} {get_localzone().tzname(printer.date)}",
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
    def getConnectedPorts(cls, retries=3, delay=2):
        """Detects all available printer ports with retries."""
        ports = []
        for _ in range(retries):
            ports = serial.tools.list_ports.comports()
            if ports:
                break
            time.sleep(delay)  # Wait for ports to initialize

        printerList = []
        for port in ports:
            hwid = port.hwid  # Get HWID
            hwid_without_location = hwid.split(' LOCATION=')[0]  # Split at ' LOCATION=' and take the first part

            port_info = {
                "device": port.device,
                "description": port.description,
                "hwid": hwid_without_location,
            }
            print(f"Port Info: {port_info}")  # Print port info for debugging

            # Check VID:PID combinations for known printers
            if (
                    "2C99:0002" in hwid  # Prusa MK3
                    or "2C99:000D" in hwid  # Prusa MK4
                    or "2C99:001A" in hwid  # Prusa MK4S
                    or "1A86:7523" in hwid  # Ender 3 and Ender 3 Pro
                    or "prusa" in port.description.lower()  # Fallback for Prusa in description
                    or "ender" in port.description.lower()  # Fallback for Ender in description
            ) and (cls.getPrinterByHwid(hwid_without_location) is None):
                printerList.append(port_info)
                print(f"Added to printerList: {port_info}")  # Print added port info

        print(f"Final printerList: {printerList}")  # Print final printer list
        return printerList
    @classmethod
    def diagnosePrinter(cls, deviceToDiagnose):  # deviceToDiagnose = port
        try:
            diagnoseString = ""
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.device == deviceToDiagnose:
                    diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
                    hwid = port.hwid 
                    hwid_without_location = hwid.split(' LOCATION=')[0]
                    printerExists = cls.searchByDevice(hwid_without_location)
                    if printerExists:
                        printer = cls.query.filter_by(hwid=hwid_without_location).first()
                        diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {printer.name} <br> <b>Device:</b> {printer.device}, <br> <b>Description:</b> {printer.description}, <br><b> HWID:</b> {printer.hwid}"
            if diagnoseString == "":
                diagnoseString = "The port this printer is registered under is <b>not found</b>. Please check the connection and try again."
            # return diagnoseString
            return {
                "success": True,
                "message": "Printer successfully diagnosed.",
                "diagnoseString": diagnoseString,
            }

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500

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

    @classmethod
    def deletePrinter(cls, printerid):
        try:
            # ser = serial.Serial(cls.query.get(printerid).device, 115200, timeout=1)
            # if(ser and ser.isOpen()):
            ports = Printer.getConnectedPorts()
            for port in ports:
                hwid = port["hwid"] # get hwid 
                if hwid == cls.query.get(printerid).hwid:
                    ser = serial.Serial(port["device"], 115200, timeout=1)
                    ser.close()
                    break 
                
            # ser.close()

            printer = cls.query.get(printerid)
            db.session.delete(printer)
            db.session.commit()
            return {"success": True, "message": "Printer successfully deleted."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to delete printer. Database error"}),
                500,
            )

    @classmethod
    def editName(cls, printerid, name):
        try:
            printer = cls.query.get(printerid)
            printer.name = name
            db.session.commit()
            return {"success": True, "message": "Printer name successfully updated."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to update printer name. Database error"}),
                500,
            )

    @classmethod
    def editPort(cls, printerid, printerport):
        try:
            ports = Printer.getConnectedPorts()
            for port in ports:
                hwid = port['hwid'] # get hwid 
                # hwid_parts = hwid.split('-')  # Replace '-' with the actual separator
                # hwid_without_location = '-'.join(hwid_parts[:-1])
                if hwid == cls.query.get(printerid).hwid:
                    ser = serial.Serial(port["device"], 115200, timeout=1)
                    ser.close()
                    break 
    # Your existing editPort code here...)
            printer = cls.query.get(printerid)
            printer.device = printerport
            db.session.commit()
            
            current_app.socketio.emit(
                "port_repair", {"printer_id": printerid, "device": printerport}
            )
            return {"success": True, "message": "Printer port successfully updated."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to update printer port. Database error"}),
                500,
            )
            
    @classmethod 
    def moveHead(cls, device):
        ser = serial.Serial(device, 115200, timeout=1)
        # message = "G91\nG1 Z10 F3000\nG90"
        message = "G28"
         # Encode and send the message to the printer.
        # time.sleep(1)
        ser.write(f"{message}\n".encode("utf-8"))
            # Sleep the printer to give it enough time to get the instruction.
            # time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
        # while True:
            # logic here about time elapsed since last response

        response = ser.readline().decode("utf-8").strip()
        if "error" in response:
            return "none"
            # if "ok" in response:
            #     break
        ser.close()
        return 
        
    def connect(self):
        if (self.emulated):
            self.socketio.emit("print", {"command": "M114"})
            return "ok"
        
        try:
            self.ser = serial.Serial(self.device, 115200, timeout=10)
            self.ser.write(f"M155 S5\n".encode("utf-8"))
        except Exception as e:
            self.setError(e)
            return "error"

    def disconnect(self):
        if self.ser:
            # self.ser.write(f"M155 S0\n".encode("utf-8"))
            self.ser.close()
            self.setSer(None)

    def reset(self):
        self.sendGcode("G28")
        self.sendGcode("G92 E0")

    # Function to send gcode commands
    def sendGcode(self, message, logger=None):
        try:
            # Encode and send the message to the printer.
            self.ser.write(f"{message}\n".encode("utf-8"))
            if logger: logger.debug(f"Command: {message}")
            # Sleep the printer to give it enough time to get the instruction.
            # time.sleep(0.1)
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                if self.terminated==1:
                    return 
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()
                if logger: logger.debug(f"Received: {response}")
                if response == "":
                    if self.prevMes == "M602":
                        self.responseCount = 0
                        # break
                    else: 
                        self.responseCount+=1 
                        if self.responseCount>=10:
                            self.setError("No response from printer")
                            raise Exception("No response from printer")

                elif "error" in response.lower():
                    self.setError(response)
                    break
                else:
                    self.responseCount = 0

                if ("T:" in response) and ("B:" in response):
                    # Extract the temperature values using regex
                    temp_t = re.search(r'T:(\d+.\d+)', response)
                    temp_b = re.search(r'B:(\d+.\d+)', response)
                    if temp_t and temp_b:
                        self.setTemps(temp_t.group(1), temp_b.group(1))

                if "ok" in response:
                    if logger: logger.info(f"Command: {message}, Received: {response}")
                    else: print(f"Command: {message}, Received: {response}")
                    break
        except Exception as e:
            if logger: logger.error(e)
            self.setError(e)
            return "error"

    def gcodeEnding(self, message):
        try: 
            self.ser.write(f"{message}\n".encode("utf-8"))
            # Save and print out the response from the printer. We can use this for error handling and status updates.
            while True:
                if self.terminated==1:
                    return 
                # logic here about time elapsed since last response
                response = self.ser.readline().decode("utf-8").strip()

                if response == "":
                    self.responseCount += 1
                    if self.responseCount >= 10:
                        self.setError("No response from printer")
                        raise Exception("No response from printer")
                elif "error" in response.lower():
                    self.setError(response)
                    break
                else:
                    self.responseCount = 0
                
                if "ok" in response:
                    break
                print(f"Command: {message}, Received: {response}")
        except Exception as e:
            # self.setStatus("error")
            print(e)
            self.setError(e)
            return "error"

    def parseGcode(self, path, job):
        try:
            with open(path, "r") as g:
                # Read the file and store the lines in a list
                if self.terminated==1:
                    return
                import sys
                cwd = os.path.dirname(__file__)
                logBase = cwd.split("server")[0] + "logs"
                logFile = str(os.path.join(logBase, self.name, job.getName(), job.date.strftime('%m-%d-%Y_%H-%M-%S'), "color"))
                os.makedirs(logFile, exist_ok=True)
                logger = logging.getLogger(logFile)
                logger.setLevel(logging.DEBUG)
                console_handler = logging.StreamHandler(sys.stdout)
                console_formatter = CustomFormatter("%(asctime)s - %(levelname)s - %(module)s.py:%(lineno)d - %(message)s")
                console_handler.setFormatter(console_formatter)
                console_handler.setLevel(logging.INFO)
                logger.addHandler(console_handler)
                info_file_handler = logging.FileHandler(os.path.join(logFile,"INFO.log"), mode="w")
                info_file_handler.setLevel(logging.INFO)
                debug_file_handler = logging.FileHandler(os.path.join(logFile,"DEBUG.log"), mode="w")
                debug_file_handler.setLevel(logging.DEBUG)
                for(file_handler) in [info_file_handler, debug_file_handler]:
                    file_handler.setFormatter(console_formatter)
                    logger.addHandler(file_handler)

                logger.info(f"Starting {job.name} on {self.name} at {job.date.strftime('%m-%d-%Y %H:%M:%S')}")
                lines = g.readlines()

                #  Time handling
                comment_lines = [line for line in lines if line.strip() and line.startswith(";")]

                max_layer_height = 0
                for i in reversed(range(len(comment_lines))):
                    # Check if the line contains ";LAYER_CHANGE"
                    if ";LAYER_CHANGE" in comment_lines[i]:
                        # Check if the next line exists
                        if i < len(comment_lines) - 1:
                            # Save the next line
                            line = comment_lines[i + 1]
                            # Use regex to find the numerical value after ";Z:"
                            match = re.search(r";Z:(\d+\.?\d*)", line)
                            if match:
                                max_layer_height = float(match.group(1))
                                break       
                if max_layer_height != 0:
                    job.setMaxLayerHeight(max_layer_height)
                

                total_time = job.getTimeFromFile(comment_lines)
                job.setTime(total_time, 0)
                # job.setTime(total_time, 0)

                # Only send the lines that are not empty and don't start with ";"
                # so we can correctly get the progress
                command_lines = [
                    line for line in lines if line.strip() and not line.startswith(";")
                ]
                # store the total to find the percentage later on
                total_lines = len(command_lines)
                # set the sent lines to 0
                sent_lines = 0
                # previous line to check for layer height
                prev_line = ""
                # Replace file with the path to the file. "r" means read mode. 
                # now instead of reading from 'g', we are reading line by line
                for line in lines:
                    if self.terminated==1:
                        self.handle_end_of_print(logFile, logger)
                        return "cancelled"
                    
                    # print("LINE: ", line, " STATUS: ", self.status, " FILE PAUSE: ", job.getFilePause())
                    if "layer" in line.lower() and self.status== 'colorchange' and job.getFilePause()==0 and self.colorbuff==0:
                        self.setColorChangeBuffer(1)

                    # if line contains ";LAYER_CHANGE", do job.currentLayerHeight(the next line)
                    if prev_line and ";LAYER_CHANGE" in prev_line:
                        match = re.search(r";Z:(\d+\.?\d*)", line)
                        if match:
                            current_layer_height = float(match.group(1))
                            job.setCurrentLayerHeight(current_layer_height)
                    prev_line = line

                    # remove whitespace
                    line = line.strip()
                    # Don't send empty lines and comments. ";" is a comment in gcode.
                    if ";" in line:  # Remove inline comments
                        line = line.split(";")[
                            0
                        ].strip()  # Remove comments starting with ";"

                    if len(line) == 0 or line.startswith(";"):
                        continue

                    if("M569" in line or "M75" in line) and job.getTimeStarted()==0:
                        job.setTimeStarted(1)
                        job.setTime(job.calculateEta(), 1)
                        job.setTime(datetime.now(), 2)
                 
                    res = self.sendGcode(line, logger)

                    if res == "error":
                        raise self.error
                    
                    if job.getFilePause() == 1:
                        # self.setStatus("printing")
                        job.setTime(job.colorEta(), 1)
                        job.setTime(job.calculateColorChangeTotal(), 0)
                        job.setTime(datetime.min, 3)
                        job.setFilePause(0)
                        if self.getStatus()== "complete":
                            return "cancelled"
                        self.setStatus("printing")
                    
                    if "M600" in line:
                        job.setTime(datetime.now(), 3)
                        # job.setTime(job.calculateTotalTime(), 0)
                        # job.setTime(job.updateEta(), 1)
                        self.setStatus("colorchange")
                        # self.setColorChangeBuffer(3)
                        # self.setColorChangeBuffer(1)
                        job.setFilePause(1)

                    if("M569" in line) and (job.getExtruded()==0):
                        job.setExtruded(1)
                    
                    if self.prevMes == "M602":
                        self.prevMes=""
                             
                #  software pausing        
                    if self.getStatus()== "paused":
                        # self.prevMes = "M601"
                        self.sendGcode("M601") # pause command for prusa
                        job.setTime(datetime.now(), 3)
                        while True:
                            time.sleep(1)
                            stat = self.getStatus()
                            if stat== "printing":
                                self.prevMes = "M602"

                                self.sendGcode("M602") # resume command for prusa

                                time.sleep(2)
                                job.setTime(job.colorEta(), 1)
                                job.setTime(job.calculateColorChangeTotal(), 0)
                                job.setTime(datetime.min, 3)
                                break
                    
                    # software color change
                    if self.getStatus()== "colorchange" and job.getFilePause()==0 and self.colorbuff==1:
                        job.setTime(datetime.now(), 3)
                        # job.setTime(job.calculateTotalTime(), 0)
                        # job.setTime(job.updateEta(), 1)
                        print("SENDING COLORCHANGE")
                        self.sendGcode("M600") # color change command
                        job.setTime(job.colorEta(), 1)
                        job.setTime(job.calculateColorChangeTotal(), 0)
                        job.setTime(datetime.min, 3)
                        job.setFilePause(1)
                        self.setColorChangeBuffer(0)
                        # self.setStatus("printing")

                    # Increment the sent lines
                    sent_lines += 1
                    job.setSentLines(sent_lines)
                    # Calculate the progress
                    progress = (sent_lines / total_lines) * 100

                    # Call the setProgress method
                    job.setProgress(progress)

                    # if self.getStatus() == "complete" and job.extruded != 0:
                    if self.getStatus() == "complete":
                        return "cancelled"

                    if self.getStatus() == "error":
                        return "error"
            self.handle_end_of_print(logFile, logger)
            return "complete"
        except Exception as e:
            self.setError(e)
            self.handle_end_of_print(logFile, logger)
            # self.setStatus("error")
            return "error"

    # Function to send "ending" gcode commands
    def endingSequence(self, job=None):
        try:
            # *** Ender 3 Pro ending sequence ***
            # self.gcodeEnding("G91") # Relative positioning
            # self.gcodeEnding("G1 E-2 F2700") # Retract a bit
            # self.gcodeEnding("G1 E-2 Z0.2 F2400") # Retract and raise Z
            # self.gcodeEnding("G1 X5 Y5 F3000") # Wipe out
            # self.gcodeEnding("G1 Z10") # Raise Z more
            # self.gcodeEnding("G90") # Absolute positioning
            # self.gcodeEnding("G1 X0 Y220") # Present print
            # self.gcodeEnding("M106 S0") # Turn-off fan
            # self.gcodeEnding("M104 S0") # Turn-off hotend
            # self.gcodeEnding("M140 S0") # Turn-off bed
            # self.gcodeEnding("M84 X Y E") # Disable all steppers but Z

            # *** Prusa i3 MK3 ending sequence ***
            # self.gcodeEnding("M104 S0") # turn off extruder
            # self.gcodeEnding("M140 S0") # turn off heatbed
            # self.gcodeEnding("M107") # turn off fan
            # self.gcodeEnding("G1 X0 Y210") # home X axis and push Y forward
            # self.gcodeEnding("M84") # disable motors

            # *** Prusa MK4 ending sequence ***
            # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+1, max_print_height)} F720 ; Move print head up{endif}")
            self.gcodeEnding("M104 S0")# ; turn off temperature
            self.gcodeEnding("M140 S0")# ; turn off heatbed
            self.gcodeEnding("M107")# ; turn off fan

            if job and job.getExtruded()==1:
                self.gcodeEnding("G1 X241 Y170 F3600")# ; park
            # self.gcodeEnding("{if layer_z < max_print_height}G1 Z{z_offset+min(layer_z+23, max_print_height)} F300")# ; Move print head up{endif}
                self.gcodeEnding("G4")# ; wait

            self.gcodeEnding("M900 K0")# ; reset LA
            self.gcodeEnding("M142 S36")# ; reset heatbreak target temp
            self.gcodeEnding("M84 X Y E")# ; disable motors   
            # ; max_layer_z = [max_layer_z]

        except Exception as e:
            self.setError(e)
            return "error"

    def printNextInQueue(self):
        # self.connect()
        job = self.getQueue().getNext()  # get next job
        try:
        # if self.getSer():
            # self.responseCount = 0
            # job.saveToFolder()
            # path = job.generatePath()

            self.setStatus("printing")  # set printer status to printing
            self.sendStatusToJob(job, job.id, "printing")

            begin = self.beginPrint(job)
            
            if begin==True: 
                Printer.repairPorts() 
                self.connect()
                if self.getSer():
                    self.responseCount = 0
                    job.saveToFolder()
                    path = job.generatePath()
                    verdict = self.parseGcode(path, job)  # passes file to code. returns "complete" if successful, "error" if not.
                    self.handleVerdict(verdict, job)
                    job.removeFileFromPath(path)  # remove file from folder after job complete
                else:
                    self.getQueue().deleteJob(job.id, self.id)
                    # self.setStatus("error")
                    self.setError("Printer not connected")
                    self.sendStatusToJob(job, job.id, "error")
            else: 
                self.handleVerdict("misprint", job)    

            # job.removeFileFromPath(path)  # remove file from folder after job complete
        # WHEN THE USER CLEARS THE JOB: remove job from queue, set printer status to ready.
        # else:
        #     self.getQueue().deleteJob(job.id, self.id)
        #     # self.setStatus("error")
        #     self.setError("Printer not connected")
        #     self.sendStatusToJob(job, job.id, "error")
            return
        except Exception as e:
            print(e)
            self.setErrorMessage(e)
            self.getQueue().deleteJob(job.id, self.id)
            self.setStatus("error")
            self.sendStatusToJob(job, job.id, "error")
            return 
            # self.handleVerdict("error", job)

    def setErrorMessage(self, error):
        self.error = error
        self.setStatus("error")
        current_app.socketio.emit(
            "error_update", {"printerid": self.id, "error": str(self.error)}
        )
            
    def beginPrint(self, job): 
        while True: 
            time.sleep(1)
            if job.getReleased()==1: 
                return True 
            if self.getStatus() == "complete": 
                return False

    def handle_end_of_print(self, logFile, logger = None):
        from globals import compress_with_gzip
        if not logger:
            return
        if logger:
            while logger.handlers:
                handler = logger.handlers[0]
                handler.flush()
                logger.removeHandler(handler)
                handler.close()
            for file in os.listdir(logFile):
                try:
                    if self.status == "error" or self.error is not None: compress_with_gzip(os.path.join(logFile, file))
                    os.remove(os.path.join(logFile, file))
                except Exception:
                    pass
            if not os.listdir(logFile):
                os.rmdir(logFile)
                parent_dir = os.path.dirname(logFile)
                while parent_dir and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
                    parent_dir = os.path.dirname(parent_dir)

    def handleVerdict(self, verdict, job: Job):
        cwd = os.getcwd()
        logBase = cwd.split("server")[0] + "logs"
        logFile = os.path.join(logBase, self.name, job.getName(), job.date.strftime('%m-%d-%Y_%H-%M-%S'), "color")
        infoFile = os.path.join(logFile, "INFO.log.gz")
        debugFile = os.path.join(logFile, "DEBUG.log.gz")
        if verdict == "complete":
            self.disconnect()
            self.setStatus("complete")
            self.sendStatusToJob(job, job.id, "complete")

        elif verdict == "error":
            # create issue
            from models.issues import Issue
            Issue.create_issue(f"CODE ISSUE: Print Failed: {self.name} - {job.file_name_original}", self.error, job_id=job)
            # send log to discord
            if Config['discord_enabled']:
                roleid = Config['discord_issues_role']
                role_message = '<@&{role_id}>'.format(role_id=roleid)
                from app import sync_send_discord_file
                sync_send_discord_file(infoFile, role_message)
                sync_send_discord_file(debugFile)
            self.disconnect()
            self.getQueue().deleteJob(job.id, self.id)
            self.setStatus("error")
            self.sendStatusToJob(job, job.id, "error")
            # self.setError("Error")
        elif verdict == "cancelled":
            self.endingSequence(job)
            self.sendStatusToJob(job, job.id, "cancelled")
            self.disconnect()
        elif verdict== "misprint": 
            self.sendStatusToJob(job, job.id, "cancelled")            
        return 
    
    def fileExistsInPath(self, path):
        if os.path.exists(path):
            return True

    # printer-specific classes
    def getDevice(self):
        return self.device

    def getQueue(self):
        return self.queue

    def getHwid(self):
        return self.hwid
    
    def setQueue(self, queue): 
        self.queue = queue

    # def removeJobFromQueue(self, job_id):
    #     self.queue.removeJob(job_id)

    #     current_app.socketio.emit('job_removed', {'printer_id': self.id, 'job_id': job_id})

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

    def setDevice(self, device): 
        self.device = device 

    #  now when we set the status, we can emit the status to the frontend

    def setStatus(self, newStatus):
        try:
            print("SETTING STATUS TO:", newStatus)
            if self.status == "error" and newStatus!= "error":
                Printer.hardReset(self.id, newStatus)
            else: 
                self.status = newStatus
            if current_app:
                current_app.socketio.emit(
                    "status_update", {"printer_id": self.id, "status": newStatus}
                )
        except Exception as e:
            print("Error setting status:", e)

    def setStopPrint(self, stopPrint):
        self.stopPrint = stopPrint

    def setError(self, error):
        self.disconnect()
        self.error = error
        self.setStatus("error")
        if current_app:
            current_app.socketio.emit(
                "error_update", {"printerid": self.id, "error": str(self.error)}
            )

    def sendStatusToJob(self, job, job_id, status):
        try:
            job.setStatus(status)
            data = {
                "printerid": self.id,
                "jobid": job_id,
                "status": status,  # Assuming status is accessible here
            }
            response = requests.post(f"{Config.get('base_url')}/updatejobstatus", json=data)
            if response.status_code == 200:
                print("Status sent successfully")
            else:
                print("Failed to send status:", response.text)
        except requests.exceptions.RequestException as e:
            print(f"Failed to send status to job: {e}")

    @classmethod 
    def repairPorts(cls):
        try:
            response = requests.post(f"{Config.get('base_url')}/repairports")

        except requests.exceptions.RequestException as e:
            print(f"Failed to repair ports: {e}")
            
    @classmethod 
    def hardReset(cls, printerid, status):
        try:
            response = requests.post(f"{Config.get('base_url')}/queuerestore", json={'printerid': printerid, 'status': status})

        except requests.exceptions.RequestException as e:
            print(f"Failed to repair ports: {e}")   

    def setTemps(self, extruder_temp, bed_temp):
        self.extruder_temp = extruder_temp
        self.bed_temp = bed_temp
        if current_app:
            current_app.socketio.emit(
                'temp_update', {'printerid': self.id, 'extruder_temp': self.extruder_temp, 'bed_temp': self.bed_temp})


    def setCanPause(self, canPause):
        try:
            self.canPause = canPause
            if current_app:
                current_app.socketio.emit('can_pause', {'printerid': self.id, 'canPause': canPause})
        except Exception as e:
            print('Error setting canPause:', e)

    def setColorChangeBuffer(self, buff): 
        self.colorbuff = buff
        if current_app:
            current_app.socketio.emit('color_buff', {'printerid': self.id, 'colorChangeBuffer': buff})


class CustomFormatter(logging.Formatter):
    # ANSI escape codes for colors
    lvlHash = {
        "DEBUG": "DBUG",
        "INFO": "INFO",
        "WARNING": "WARN",
        "ERROR": "EROR",
        "CRITICAL": "CRIT"
    }
    COLOR_CODES = {
        "DEBUG": "\033[94m",  # Blue
        "INFO": "\033[0m",  # white
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m"  # Magenta
    }
    RESET_CODE = "\033[0m"  # Reset to default color

    def format(self, record):
        # Apply color based on log level
        color = self.COLOR_CODES.get(record.levelname, self.RESET_CODE)
        record.levelname = self.lvlHash.get(record.levelname, record.levelname)
        message = super().format(record)
        return f"{color}{message}{self.RESET_CODE}"


            