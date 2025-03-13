import logging
import traceback
import pyvisa.errors
from Classes.Loggers.JobLogger import JobLogger
from abc import ABCMeta
import re
from datetime import datetime
from time import sleep
from globals import current_app, TemporaryTimeout
from Classes.Fabricators.Device import Device
from Classes.Jobs import Job
from Mixins.hasResponseCodes import checkTime, checkExtruderTemp, checkXYZ, checkBedTemp, checkOK


class Printer(Device, metaclass=ABCMeta):
    cancelCMD: str = "M112"
    keepAliveCMD: str = "M113 S1"
    doNotKeepAliveCMD: str = "M113 S0"
    statusCMD: str = "M115"
    getLocationCMD: str = "M114"
    pauseCMD: str = "M601"
    resumeCMD: str = "M602"
    getMachineNameCMD: str = "M997"
    startTimeCMD: str = "M75"

    callablesHashtable = {
        "M31": [checkTime],  # Print time
        "M104": [],  # Set hotend temp
        "M109": [checkExtruderTemp],  # Wait for hotend to reach target temp
        "M114": [checkXYZ],  # Get current position
        "M140": [],  # Set bed temp
        "M190": [checkBedTemp],  # Wait for bed to reach target temp
    }
    callablesHashtable = {**Device.callablesHashtable, **callablesHashtable}
    
    bedTemperature: int | float | None = None
    bedTargetTemp: float = 0.0
    nozzleTemperature: int | float |  None = None
    nozzleTargetTemp: float = 0.0

    def __init__(self, dbID, serialPort, consoleLogger=None, fileLogger=None, addLogger: bool =False, websocket_connection=None, name:str = None):
        super().__init__(dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
        self.filamentType = None
        self.filamentDiameter = None
        self.nozzleDiameter = None

    def parseGcode(self, job: Job, isVerbose: bool = False):
        assert isinstance(job, Job), f"Expected Job, got {type(job)}"
        file = job.file_path
        assert isinstance(file, str), f"Expected file to be a str, got {type(file)}"
        assert isinstance(isVerbose, bool), f"Expected isVerbose to be a bool, got {type(isVerbose)}"
        assert self.serialConnection.is_open, "Serial connection is not open"
        assert self.status == "printing", f"Printer status is {self.status}, expected printing"
        logger = None
        try:
            with open(file, "r") as g:
                # create a logger for this job

                jobName = str(job.file_name_original)
                if jobName:
                    jobName = "-".join(jobName.split(".")[0].split("_"))
                logger = JobLogger(self.name, jobName, job.date.strftime('%m-%d-%Y_%H-%M-%S'), self.serialPort, loggingLevel=logging.INFO if isVerbose else logging.WARNING, fileLogger=None)

                logger.info(f"Starting {job.name} on {self.name} at {job.date.strftime('%m-%d-%Y %H:%M:%S')}")
                # Read the file and store the lines in a list
                if self.status == "cancelled":
                    self.sendGcode(self.cancelCMD, isVerbose, logger)
                    self.verdict = "cancelled"
                    logger.info("Job cancelled")
                    logger.nukeLogs()
                    return True

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
                current_app.socketio.emit("console_update", {"message": "Starting Job", "level": "info", "printerid": self.dbID})
                for line in lines:
                    if self.status == "cancelled":
                        self.sendGcode(self.cancelCMD, isVerbose, logger)
                        self.verdict = "cancelled"
                        logger.info("Job cancelled")
                        logger.nukeLogs()
                        return True

                        # print("LINE: ", line, " STATUS: ", self.status, " FILE PAUSE: ", job.getFilePause())
                    if "layer" in line.lower() and self.status == 'colorchange':
                        #TODO: implement color change
                        pass

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
                    if job.getTimeStarted() == 0 and ("M75" in line or self.startTimeCMD in line):
                        job.setTimeStarted(1)
                        job.setTime(job.calculateEta(), 1)
                        job.setTime(datetime.now(), 2)
                        if current_app:
                            current_app.socketio.emit("console_update", {"message": "Fabricating...", "level": "info", "printerid": self.dbID})

                    assert self.sendGcode(line, logger=logger), f"Failed to send {line}"

                    if job.getFilePause() == 1:
                        # self.setStatus("printing")
                        job.setTime(job.colorEta(), 1)
                        job.setTime(job.calculateColorChangeTotal(), 0)
                        job.setTime(datetime.min, 3)
                        job.setFilePause(0)
                        if self.status == "cancelled":
                            self.sendGcode(self.cancelCMD, logger=logger)
                            self.verdict = "cancelled"
                            logger.info("Job cancelled")
                            logger.nukeLogs()
                            return True
                        self.status = "printing"

                    if "M600" in line:
                        job.setTime(datetime.now(), 3)
                        # job.setTime(job.calculateTotalTime(), 0)
                        # job.setTime(job.updateEta(), 1)
                        self.status = "colorchange"
                        # self.setColorChangeBuffer(3)
                        # self.setColorChangeBuffer(1)
                        job.setFilePause(1)

                    if ("M569" in line) and (job.getExtruded() == 0):
                        job.setExtruded(1)

                    #  software pausing
                    if self.status == "paused":
                        self.pause()
                        job.setTime(datetime.now(), 3)
                        while self.status == "paused":
                            sleep(.5)
                            readline = self.serialConnection.read().strip()
                            if readline:
                                logger.debug(readline)
                                if "T:" in readline and "B:" in readline:
                                    logger.debug(f"Temperature line: {readline}")
                                    self.handleTempLine(readline, logger)
                            if self.status == "cancelled":
                                self.sendGcode(self.cancelCMD)
                                self.verdict = "cancelled"
                                logger.info("Job cancelled")
                                logger.nukeLogs()
                                current_app.socketio.emit("console_update", {"message": "Job cancelled", "level": "info", "printerid": self.dbID})
                                return True
                            elif self.status == "printing":
                                self.resume()
                                job.setTime(job.colorEta(), 1)
                                job.setTime(job.calculateColorChangeTotal(), 0)
                                job.setTime(datetime.min, 3)
                    # software color change
                    if self.status == "colorchange" and job.getFilePause() == 0:
                        job.setTime(datetime.now(), 3)
                        # job.setTime(job.calculateTotalTime(), 0)
                        # job.setTime(job.updateEta(), 1)
                        print("SENDING COLORCHANGE")
                        self.sendGcode("M600")  # color change command
                        job.setTime(job.colorEta(), 1)
                        job.setTime(job.calculateColorChangeTotal(), 0)
                        job.setTime(datetime.min, 3)
                        job.setFilePause(1)
                        #self.setColorChangeBuffer(0)
                        # self.setStatus("printing")

                    # Increment the sent lines
                    sent_lines += 1
                    job.setSentLines(sent_lines)
                    # Calculate the progress
                    progress = (sent_lines / total_lines) * 100

                    # Call the setProgress method
                    job.setProgress(progress)

                    # if self.status == "complete" and job.extruded != 0:
                    if self.status == "complete":
                        self.verdict = "complete"
                        logger.info("Job complete")
                        logger.nukeLogs()
                        current_app.socketio.emit("console_update", {"message": "Job complete", "level": "info", "printerid": self.dbID})
                        return True

                    if self.status == "error":
                        self.verdict = "error"
                        logger.error("Job error")
                        logger.nukeLogs(error=True)
                        current_app.socketio.emit("console_update", {"message": "Job error", "level": "error", "printerid": self.dbID})
                        return True
            self.verdict = "complete"
            self.status = "complete"
            logger.info("Job complete")
            logger.nukeLogs()
            current_app.socketio.emit("console_update", {"message": "Job complete", "level": "info", "printerid": self.dbID})
            return True
        except Exception as e:
            self.verdict = "error"
            current_app.socketio.emit("error_update",{"fabricator_id": self.dbID, "job_id": job.id, "error": str(e)})
            current_app.socketio.emit("console_update", {"message": "Job error", "level": "error", "printerid": self.dbID})
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)
            logger.nukeLogs(error=True)
            return e
        
    def sendGcode(self, gcode: bytes | str, isVerbose: bool = True, logger: JobLogger = None) -> bool:
        """
        Method to send gcode to the printer
        :param bytes | str | LiteralString gcode: the line of gcode to send to the printer
        :param bool isVerbose: whether to log or not
        :param JobLogger logger: the logger to use
        :rtype: bool
        """
        if logger is None: logger = self.logger
        assert self.serialConnection is not None, "Serial connection is None"
        assert self.serialConnection.is_open, "Serial connection is not open"
        if isinstance(gcode, bytes):
            gcode = gcode.decode("utf-8")
        assert isinstance(gcode, str), f"Expected string, got {type(gcode)}"
        callables = self.callablesHashtable.get(self.extractIndex(gcode, logger), [checkOK])
        current_app.socketio.emit("gcode_line", {"line": (gcode.decode() if isinstance(gcode, bytes) else gcode).strip(), "printerid": self.dbID})
        self.serialConnection.write(gcode)
        line = ''
        for func in callables:
            while True:
                if self.status == "cancelled": return True
                try:
                    line = self.serialConnection.read()
                    decLine = line.strip()
                    if "processing" in decLine or "echo" in decLine: continue
                    if "T:" in decLine and "B:" in decLine:
                        self.handleTempLine(decLine, logger)
                        if func != checkBedTemp and func != checkExtruderTemp and "ok" not in decLine.lower():
                            continue
                    if func(line, self):
                        break
                    logger.debug(f"{gcode.strip()}: {decLine}")
                    # current_app.socketio.emit("console_update",{"message": decLine, "level": "debug", "printerid": self.dbID})
                except UnicodeDecodeError:
                    logger.debug(f"{gcode.strip()}: {line.strip()}")
                    # current_app.socketio.emit("console_update",{"message": gcode.strip(), "level": "debug", "printerid": self.dbID})
                except pyvisa.errors.VisaIOError as e:
                    logger.critical(f"timeout exceeded: {gcode.strip()}, timeout length: {self.serialConnection.timeout} milliseconds")
                    if current_app: return current_app.handle_errors_and_logging(e, logger)
                    else: print(traceback.format_exc())
                    return False
                except Exception as e:
                    if current_app: return current_app.handle_errors_and_logging(e, logger)
                    else: print(traceback.format_exc())
                    return False
        if not callables:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.strip()}: ok", "level": "info", "printerid": self.dbID})
            logger.info(f"{gcode.strip()}: ok")
        else:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}", "level": "info", "printerid": self.dbID})
            logger.info(f"{gcode.strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}")
        return True

    def changeFilament(self, filamentType: str, filamentDiameter: float, logger: JobLogger = None):
        """
        Method to change filament
        :param str filamentType: type of plastic the filament is made of
        :param float filamentDiameter:  diameter of the filament in mm
        :param JobLogger logger: the logger to use
        """
        if not isinstance(filamentDiameter, float):
            filamentDiameter = float(filamentDiameter)
        try:
            assert self.status == "idle", "Printer is not idle"
            self.filamentType = filamentType
            self.filamentDiameter = filamentDiameter
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def changeNozzle(self, nozzleDiameter: float, logger: JobLogger = None):
        """
        Method to change nozzle size
        :param float nozzleDiameter: The diameter of the nozzle in mm
        :param JobLogger logger: the logger to use
        """
        try:
            if not isinstance(nozzleDiameter, float):
                nozzleDiameter = float(nozzleDiameter)
            assert self.status == "idle", "Printer is not idle"
            self.nozzleDiameter = nozzleDiameter
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def handleTempLine(self, line: str , logger: JobLogger = None) -> None:
        """
        Method to handle temperature lines in the serial response
        :param str line: the line to parse
        :param JobLogger logger: the logger to use
        """
        try:
            temp_t = re.search(r'T:(\d+.\d+)', line)
            temp_b = re.search(r'B:(\d+.\d+)', line)
            if not temp_t:
                temp_t = re.search(r'T:(\d+)', line)
            if not temp_b:
                temp_b = re.search(r'B:(\d+)', line)
            if temp_t:
                self.nozzleTemperature = float(temp_t.group(1))
            if temp_b:
                self.bedTemperature = float(temp_b.group(1))
            if current_app:
                current_app.socketio.emit('temp_update', {'printerid': self.dbID, 'extruder_temp': self.nozzleTemperature, 'bed_temp': self.bedTemperature})
            if logger:
                logger.debug(f"temp update: nozzle: {self.nozzleTemperature}, bed: {self.bedTemperature}")
        except ValueError:
            pass
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def extractIndex(self, gcode: str, logger=None) -> str:
        """
        Method to extract the index of the gcode for use in the callablesHashtable
        :param str gcode: the line of gcode to extract the index from
        :param JobLogger | None logger: the logger to use
        :rtype: str
        """
        if logger is None: logger = self.logger
        hashIndex = gcode.split("\n")[0].split(" ")[0]

        match hashIndex:
            case "M104":
                try:
                    temp = gcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = gcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    self.nozzleTargetTemp = float(temp)
            case "M140":
                try:
                    temp = gcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = gcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    self.bedTargetTemp = float(temp)
            case "M109":
                try:
                    temp = gcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = gcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    if logger is not None: logger.info(f"Waiting for hotend temperature to stabilize at {temp}\u00B0C...")
                    self.nozzleTargetTemp = float(temp)
                    current_app.socketio.emit("console_update",
                                          {"message": f"Waiting for hotend temperature to stabilize at {temp}\u00B0C...", "level": "info",
                                           "printerid": self.dbID})
                else:
                    if logger is not None: logger.info("Waiting for hotend temperature to stabilize...")
                    current_app.socketio.emit("console_update",
                                          {"message": "Waiting for hotend temperature to stabilize...", "level": "info",
                                           "printerid": self.dbID})
            case "M190":
                try:
                    temp = gcode.split("S")[1].split("\n")[0]
                except IndexError:
                    temp = None
                if temp:
                    if logger is not None: logger.info(f"Waiting for bed temperature to stabilize at {temp}\u00B0C...")
                    self.bedTargetTemp = float(temp)
                    current_app.socketio.emit("console_update",
                                          {"message": f"Waiting for bed temperature to stabilize at {temp}\u00B0C...", "level": "info",
                                           "printerid": self.dbID})
                else:
                    if logger is not None: logger.info("Waiting for bed temperature to stabilize...")
                    current_app.socketio.emit("console_update",
                                          {"message": "Waiting for bed temperature to stabilize...", "level": "info",
                                           "printerid": self.dbID})
            case "G28":
                if logger is not None: logger.info("Homing...")
                current_app.socketio.emit("console_update", {"message": "Homing...", "level": "info", "printerid": self.dbID})
        return hashIndex

    def pause(self, logger: JobLogger = None):
        if not self.pauseCMD:
            if self.logger is not None: self.logger.error("Pause command not implemented.")
            return True
        try:
            assert self.pauseCMD is not None
            assert isinstance(self, Device)
            assert self.serialConnection is not None
            assert self.serialConnection.is_open
            if hasattr(self, "keepAliveCMD") and self.keepAliveCMD:
                self.sendGcode(self.keepAliveCMD)
            self.sendGcode(self.pauseCMD)
            if self.logger is not None: self.logger.info("Job Paused")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def resume(self, logger: JobLogger = None) -> bool:
        if self.resumeCMD is None:
            if self.logger is not None: self.logger.error("Resume command not implemented.")
            return False
        try:
            assert isinstance(self, Device), "self is not an instance of Device"
            assert self.serialConnection is not None, "Serial connection is None"
            assert self.serialConnection.is_open, "Serial connection is not open"
            if hasattr(self, "doNotKeepAliveCMD") and self.doNotKeepAliveCMD: self.sendGcode(self.doNotKeepAliveCMD, False)
            self.sendGcode(self.resumeCMD, False)
            if self.logger is not None: self.logger.info("Job Resumed")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def connect(self) -> bool:
        assert super().connect(), "Failed to connect to printer"
        try:
            assert self.serialConnection is not None, "Serial connection is None"
            assert self.serialConnection.is_open, "Serial connection is not open"
            for timeout in [1500, 3500, 10000]:
                try:
                    with TemporaryTimeout(self.serialConnection, timeout):
                        response = self.serialConnection.query("M115 S1")
                        assert response is not None
                        break
                except AssertionError as e:
                    # failed to connect, response is empty. retrying...
                    current_app.socketio.emit("registration_failure", {"printerid": self.dbID, "message": f"Failed to connect to printer: printer gave empty response. {'Retrying...' if timeout != 10000 else 'Please power cycle the printer and try again.'}", "level": f"{'warning' if timeout != 10000 else 'error'}"})
                    if timeout == 10000:
                        return current_app.handle_errors_and_logging(e, self.logger)
                except pyvisa.errors.VisaIOError as e:
                    # failed to connect, no response. retrying...
                    current_app.socketio.emit("registration_failure", {"printerid": self.dbID, "message": f"Failed to connect to printer: printer gave no response within timeout. {'Retrying...' if timeout != 10000 else 'Please power cycle the printer and try again.'}", "level": f"{'warning' if timeout != 10000 else 'error'}"})
                    if timeout == 10000:
                        return current_app.handle_errors_and_logging(e, self.logger)

            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def disconnect(self) -> bool:
        try:
            if self.serialConnection and self.serialConnection.is_open:
                self.sendGcode("M155 S100", False)
                self.sendGcode("M155 S0", False)
                self.sendGcode("M104 S0", False)
                self.sendGcode("M140 S0", False)
                self.sendGcode("M84", False)
                self.serialConnection.close()
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)