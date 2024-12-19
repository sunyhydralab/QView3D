import traceback
import sys
from Classes.Loggers.JobLogger import JobLogger
from abc import ABCMeta
import re
from datetime import datetime
from time import sleep
from globals import current_app
from Classes.Fabricators.Device import Device
from Classes.Jobs import Job
from Mixins.hasResponseCodes import checkTime, checkExtruderTemp, checkXYZ, checkBedTemp, checkOK


class Printer(Device, metaclass=ABCMeta):
    cancelCMD: bytes = b"M112\n"
    keepAliveCMD: bytes = b"M113 S1\n"
    doNotKeepAliveCMD: bytes = b"M113 S0\n"
    statusCMD: bytes = b"M115\n"
    getLocationCMD: bytes = b"M114\n"
    pauseCMD: bytes = b"M601\n"
    resumeCMD: bytes = b"M602\n"
    getMachineNameCMD: bytes = b"M997\n"
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
    nozzleTemperature: int | float |  None = None

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
        try:
            with open(file, "r") as g:
                # create a logger for this job

                jobName = str(job.file_name_original)
                if jobName:
                    jobName = "-".join(jobName.split(".")[0].split("_"))
                logger = JobLogger(self.name, jobName, job.date.strftime('%m-%d-%Y_%H-%M-%S'), self.serialPort.device, consoleLogger=sys.stdout if isVerbose else None, fileLogger=None)

                logger.info(f"Starting {job.name} on {self.name} at {job.date.strftime('%m-%d-%Y %H:%M:%S')}")
                # Read the file and store the lines in a list
                if self.status == "cancelled":
                    self.sendGcode(self.cancelCMD)
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
                        self.sendGcode(self.cancelCMD)
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
                            self.sendGcode(self.cancelCMD)
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
                            readline = self.serialConnection.readline().decode("utf-8").strip()
                            if readline:
                                logger.debug(readline)
                                if "T:" in readline and "B:" in readline:
                                    logger.debug(f"Temperature line: {readline}")
                                    self.handleTempLine(readline)
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
                        current_app.socketio.emit("console_update", {"message": "Job error", "level": "info", "printerid": self.dbID})
                        return False
            self.verdict = "complete"
            self.status = "complete"
            logger.info("Job complete")
            logger.nukeLogs()
            current_app.socketio.emit("console_update", {"message": "Job complete", "level": "info", "printerid": self.dbID})
            return True
        except Exception as e:
            # self.setStatus("error")
            return current_app.handle_errors_and_logging(e, self.logger)
        
    def sendGcode(self, gcode: bytes | str, isVerbose: bool = False, logger: JobLogger = None) -> bool:
        """
        Method to send gcode to the printer
        :param bytes | str | LiteralString gcode: the line of gcode to send to the printer
        :param bool isVerbose: whether to log or not
        :param JobLogger logger: the logger to use
        :rtype: bool
        """
        assert self.serialConnection is not None, "Serial connection is None"
        assert self.serialConnection.is_open, "Serial connection is not open"
        if isinstance(gcode, str):
            if gcode[-1] != "\n": gcode += "\n"
            gcode = gcode.encode("utf-8")
        assert isinstance(gcode, bytes), f"Expected bytes, got {type(gcode)}"
        assert isinstance(isVerbose, bool), f"Expected bool, got {type(isVerbose)}"
        callables = self.callablesHashtable.get(self.extractIndex(gcode), [checkOK])
        current_app.socketio.emit("gcode_line", {"line": (gcode.decode() if isinstance(gcode, bytes) else gcode).strip(), "printerid": self.dbID})
        self.serialConnection.write(gcode)
        line = ''
        for func in callables:
            while True:
                if self.status == "cancelled": return True
                try:
                    line = self.serialConnection.readline()
                    decLine = line.decode("utf-8").strip()
                    if "processing" in decLine or "echo" in decLine: continue
                    if "T:" in decLine and "B:" in decLine:
                        self.handleTempLine(decLine)
                        if func != checkBedTemp and func != checkExtruderTemp and "ok" not in decLine.lower():
                            continue
                    if func(line, self):
                        break
                    if logger is not None: logger.debug(f"{gcode.decode().strip()}: {decLine}")
                    # current_app.socketio.emit("console_update",{"message": decLine, "level": "debug", "printerid": self.dbID})
                except UnicodeDecodeError:
                    if logger is not None: logger.debug(f"{gcode.decode().strip()}: {line.strip()}")
                    else: print(f"{gcode.decode().strip()}: {line.strip()}")
                    # current_app.socketio.emit("console_update",{"message": gcode.decode().strip(), "level": "debug", "printerid": self.dbID})
                except Exception as e:
                    if current_app: return current_app.handle_errors_and_logging(e, self.logger)
                    elif logger is not None: logger.error(e)
                    else: print(traceback.format_exc())
                    return False
        if not callables:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.decode().strip()}: ok", "level": "info", "printerid": self.dbID})
            if logger is not None: logger.info(f"{gcode.decode().strip()}: ok")
        else:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.decode().strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}", "level": "info", "printerid": self.dbID})
            if logger is not None: logger.info(
                f"{gcode.decode().strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}")
        return True

    def changeFilament(self, filamentType: str, filamentDiameter: float):
        """
        Method to change filament
        :param str filamentType: type of plastic the filament is made of
        :param float filamentDiameter:  diameter of the filament in mm
        """
        if not isinstance(filamentDiameter, float):
            filamentDiameter = float(filamentDiameter)
        try:
            assert self.status == "idle", "Printer is not idle"
            self.filamentType = filamentType
            self.filamentDiameter = filamentDiameter
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger)

    def changeNozzle(self, nozzleDiameter: float):
        """
        Method to change nozzle size
        :param float nozzleDiameter: The diameter of the nozzle in mm
        """
        try:
            if not isinstance(nozzleDiameter, float):
                nozzleDiameter = float(nozzleDiameter)
            assert self.status == "idle", "Printer is not idle"
            self.nozzleDiameter = nozzleDiameter
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger)

    def handleTempLine(self, line: str) -> None:
        """
        Method to handle temperature lines in the serial response
        :param str line: the line to parse
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
                current_app.socketio.emit('temp_update', {'printerid': self.dbID, 'extruder_temp': self.nozzleTemperature,
                                                          'bed_temp': self.bedTemperature})
        except ValueError:
            pass
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger)

    def extractIndex(self, gcode: bytes, logger=None) -> str:
        """
        Method to extract the index of the gcode for use in the callablesHashtable
        :param bytes gcode: the line of gcode to extract the index from
        :param Logger | JobLogger | None logger: the logger to use
        :rtype: str
        """
        if logger is None: logger = self.logger
        hashIndex = gcode.decode().split("\n")[0].split(" ")[0]

        if hashIndex == "M109":
            try:
                temp = gcode.decode().split("S")[1].split("\n")[0]
            except IndexError:
                try:
                    temp = gcode.decode().split("R")[1].split("\n")[0]
                except IndexError:
                    temp = None
            if temp:
                if logger is not None: logger.info(f"Waiting for hotend temperature to stabilize at {temp}\u00C2\u00B0C...")
                current_app.socketio.emit("console_update",
                                      {"message": f"Waiting for hotend temperature to stabilize at {temp}\u00B0C...", "level": "info",
                                       "printerid": self.dbID})
            else:
                if logger is not None: logger.info("Waiting for hotend temperature to stabilize...")
                current_app.socketio.emit("console_update",
                                      {"message": "Waiting for hotend temperature to stabilize...", "level": "info",
                                       "printerid": self.dbID})
        if hashIndex == "M190":
            try:
                temp = gcode.decode().split("S")[1].split("\n")[0]
            except IndexError:
                temp = None
            if temp:
                if self.logger is not None: self.logger.info(f"Waiting for bed temperature to stabilize at {temp}\u00C2\u00B0C...")
                current_app.socketio.emit("console_update",
                                      {"message": f"Waiting for bed temperature to stabilize at {temp}\u00B0C...", "level": "info",
                                       "printerid": self.dbID})
            else:
                if self.logger is not None: self.logger.info("Waiting for bed temperature to stabilize...")
                current_app.socketio.emit("console_update",
                                      {"message": "Waiting for bed temperature to stabilize...", "level": "info",
                                       "printerid": self.dbID})
        elif hashIndex == "G28":
            if self.logger is not None: self.logger.info("Homing...")
            current_app.socketio.emit("console_update",
                                      {"message": "Homing...", "level": "info", "printerid": self.dbID})
        return hashIndex

    def pause(self):
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
            return current_app.handle_errors_and_logging(e, self.logger)

    def resume(self) -> bool:
        if self.resumeCMD is None:
            if self.logger is not None: self.logger.error("Resume command not implemented.")
            return False
        try:
            assert isinstance(self, Device), "self is not an instance of Device"
            assert self.serialConnection is not None, "Serial connection is None"
            assert self.serialConnection.is_open, "Serial connection is not open"
            if hasattr(self, "doNotKeepAliveCMD") and self.doNotKeepAliveCMD: self.sendGcode(self.doNotKeepAliveCMD)
            self.sendGcode(self.resumeCMD)
            if self.logger is not None: self.logger.info("Job Resumed")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def connect(self) -> bool:
        super().connect()
        try:
            if self.serialConnection and self.serialConnection.is_open:
                self.sendGcode(b"M155 S1\n", isVerbose=True)
                return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def disconnect(self) -> None:
        if self.serialConnection and self.serialConnection.is_open:
            self.sendGcode(b"M155 S100\n")
            self.sendGcode(b"M155 S0\n")
            self.sendGcode(b"M104 S0\n")
            self.sendGcode(b"M140 S0\n")
            self.sendGcode(b"M84\n")
            self.serialConnection.close()