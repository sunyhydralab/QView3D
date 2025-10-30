import traceback
import sys
from abc import ABCMeta
from services.logger import logger
import re
from datetime import datetime
from time import sleep, time
from services.app_service import current_app
from Classes.Fabricators.Device import Device
from Classes.Jobs import Job
from Mixins.hasResponseCodes import checkTime, checkExtruderTemp, checkXYZ, checkBedTemp, checkOK, checkFirmware
from serial.serialutil import SerialException, SerialTimeoutException


class Printer(Device, metaclass=ABCMeta):
    """
    Abstract base class for 3D printers that use G-code communication.

    Extends the Device class to provide printer-specific functionality including
    G-code streaming, temperature monitoring, print job management, and firmware
    communication. This class handles the low-level serial communication protocol
    with Marlin-based firmware.

    Attributes:
        cancelCMD (bytes): Emergency stop command (M112)
        keepAliveCMD (bytes): Enable host keepalive messages every 2 seconds (M113 S2)
        doNotKeepAliveCMD (bytes): Disable keepalive messages (M113 S0)
        statusCMD (bytes): Get firmware info command (M115)
        getLocationCMD (bytes): Get current XYZ position (M114)
        pauseCMD (bytes): Pause print command (M601)
        resumeCMD (bytes): Resume print command (M602)
        getMachineNameCMD (bytes): Get machine name (M997)
        startTimeCMD (str): Start print timer command (M75)

        bedTemperature (float): Current bed temperature in Celsius
        bedTargetTemp (float): Target bed temperature in Celsius
        nozzleTemperature (float): Current nozzle temperature in Celsius
        nozzleTargetTemp (float): Target nozzle temperature in Celsius
        filamentType (str): Type of filament loaded (e.g., PLA, PETG, ABS)
        filamentDiameter (float): Diameter of filament in mm (typically 1.75 or 2.85)
        nozzleDiameter (float): Diameter of nozzle in mm (e.g., 0.4, 0.6, 0.8)

    Methods:
        parseGcode(job): Stream and execute G-code commands from a job file
        sendGcode(gcode, logger): Send a single G-code command and wait for response
        handleTempLine(line): Parse temperature data from printer responses
        pause(): Pause the current print job
        resume(): Resume a paused print job
        changeFilament(type, diameter): Update filament settings
        changeNozzle(diameter): Update nozzle diameter setting

    Notes:
        - Uses synchronous command/response protocol: waits for "ok" before next command
        - Implements validators to check specific responses (temps, positions, firmware)
        - Supports auto-temperature reporting (M155) for continuous monitoring
        - Keepalive messages prevent timeouts during heating and bed leveling
    """

    # G-code command constants (Marlin firmware)
    cancelCMD: bytes = b"M112\n"  # Emergency stop - halts all movement immediately
    keepAliveCMD: bytes = b"M113 S2\n"  # Send keepalive every 2 seconds during long operations
    doNotKeepAliveCMD: bytes = b"M113 S0\n"  # Disable keepalive messages
    statusCMD: bytes = b"M115\n"  # Request firmware name, version, and capabilities
    getLocationCMD: bytes = b"M114\n"  # Get current XYZ position and extruder state
    pauseCMD: bytes = b"M601\n"  # Pause print (filament change pause)
    resumeCMD: bytes = b"M602\n"  # Resume print after pause
    getMachineNameCMD: bytes = b"M997\n"  # Get machine name
    startTimeCMD: str = "M75"  # Start/resume print timer

    # Validator hashtable: maps G-code commands to validation functions
    # Validators check if the printer's response indicates successful command execution
    callablesHashtable = {
        "M31": [checkTime],  # Print time - validates time format
        "M104": [],  # Set hotend temp - no validation needed (fire and forget)
        "M109": [checkExtruderTemp],  # Wait for hotend - validates temp reached target
        "M113": [checkOK],  # Host keepalive - validates "ok" response
        "M114": [checkXYZ],  # Get current position - validates X:Y:Z: format
        "M115": [checkFirmware],  # Get firmware info - reads all Cap: lines until "ok"
        "M140": [],  # Set bed temp - no validation needed (fire and forget)
        "M155": [checkOK],  # Temperature auto-report - validates "ok" response
        "M190": [checkBedTemp],  # Wait for bed - validates bed temp reached target
    }
    # Merge with parent Device class validators
    callablesHashtable = {**Device.callablesHashtable, **callablesHashtable}

    # Temperature tracking (updated continuously via M155 auto-reporting)
    bedTemperature: int | float | None = None  # Current bed temperature
    bedTargetTemp: float = 0.0  # Target bed temperature
    nozzleTemperature: int | float |  None = None  # Current nozzle temperature
    nozzleTargetTemp: float = 0.0  # Target nozzle temperature

    def __init__(self, dbID, serialPort, consoleLogger=None, fileLogger=None, addLogger: bool =False, websocket_connection=None, name:str = None):
        """
        Initialize a Printer instance.

        :param int dbID: Database ID of the printer
        :param ListPortInfo serialPort: Serial port object for communication
        :param Logger consoleLogger: Optional console logger instance
        :param Logger fileLogger: Optional file logger instance
        :param bool addLogger: Whether to add a logger to this printer
        :param WebSocket websocket_connection: Optional WebSocket connection for emulator
        :param str name: Optional friendly name for the printer
        """
        super().__init__(dbID, serialPort, consoleLogger=consoleLogger, fileLogger=fileLogger, addLogger=addLogger, websocket_connection=websocket_connection, name=name)
        # Filament and nozzle properties (set by user, affects print settings)
        self.filamentType = None  # PLA, PETG, ABS, etc.
        self.filamentDiameter = None  # 1.75mm or 2.85mm typically
        self.nozzleDiameter = None  # 0.4mm, 0.6mm, 0.8mm, etc.

    def parseGcode(self, job: Job):
        """
        Stream and execute G-code commands from a job file to the printer.

        This method performs a two-pass process:
        1. First pass: Scan file for metadata (layer heights, time estimates)
        2. Second pass: Stream G-code line-by-line to printer with synchronous execution

        The method enables auto-temperature reporting (M155) and keepalive messages (M113)
        at the start, and disables them when printing completes or errors occur.

        :param Job job: The print job containing the G-code file path
        :return: True if print completed successfully, False if error occurred
        :rtype: bool

        :raises AssertionError: If job is invalid, serial connection closed, or printer not in printing state
        :raises Exception: For any errors during G-code streaming (caught and logged)

        Notes:
            - Supports pause/resume, color changes, and cancellation during printing
            - Updates job progress in real-time via Job.setProgress()
            - Handles temperature monitoring via handleTempLine()
            - Always disables keepalive in finally block to prevent serial timeouts after print
        """
        assert isinstance(job, Job), f"Expected Job, got {type(job)}"
        file = job.file_path
        assert isinstance(file, str), f"Expected file to be a str, got {type(file)}"
        assert self.serialConnection.is_open, "Serial connection is not open"
        assert self.status == "printing", f"Printer status is {self.status}, expected printing"
        try:
            with open(file, "r") as g:
                # Create a logger for this job (currently simplified - no verbose logging)
                jobName = str(job.file_name_original)
                if jobName:
                    jobName = "-".join(jobName.split(".")[0].split("_"))
                logger = None
                job.job_logger = logger

                # Early cancellation check
                if self.status == "cancelled":
                    self.sendGcode(self.cancelCMD)
                    self.verdict = "cancelled"
                    logger.log("Job cancelled")
                    return True

                # ===== FIRST PASS: Metadata Extraction =====
                # Stream through file once to gather print info without loading entire file into memory
                total_lines = 0  # Count of actual G-code commands (excluding comments)
                max_layer_height = 0  # Maximum Z height for progress tracking
                max_layer_height_candidate = None  # Temporary holder for layer change detection
                comment_lines = []  # Store comment lines for time estimation

                # Stream through file to gather metadata
                for line in g:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith(";"):
                        if line_stripped.startswith(";"):
                            comment_lines.append(line_stripped)
                            # Check for layer height on the fly
                            if ";LAYER_CHANGE" in line_stripped:
                                max_layer_height_candidate = line_stripped
                            elif max_layer_height_candidate and ";Z:" in line_stripped:
                                match = re.search(r";Z:(\d+\.?\d*)", line_stripped)
                                if match:
                                    max_layer_height = max(max_layer_height, float(match.group(1)))
                                max_layer_height_candidate = None
                        continue
                    total_lines += 1

                if max_layer_height != 0:
                    job.setMaxLayerHeight(max_layer_height)

                # Extract time estimate from slicer-generated comments
                total_time = job.getTimeFromFile(comment_lines)
                job.setTime(total_time, 0)

                # ===== SECOND PASS: G-code Streaming =====
                # Reset file pointer to beginning for actual printing
                g.seek(0)

                # Initialize streaming variables
                sent_lines = 0  # Track number of commands sent for progress calculation
                prev_line = ""  # Store previous line to detect layer changes
                last_progress_update = 0  # Track last progress percentage for throttling time updates
                gcode_lines_buffer = []  # Buffer for live gcode preview
                current_app.socketio.emit("console_update", {"message": "Starting Job", "level": "info", "fabricator_id": self.dbID})

                # Enable continuous temperature monitoring (M155 S100 = 100ms interval)
                # This allows M109/M190 commands to track temp progress in real-time
                print("[Printer] Enabling auto temperature reporting (M155 S100)")
                self.sendGcode("M155 S100\n", logger=self.logger)

                # Initialize time tracking before starting actual printing
                # This ensures frontend shows "00:00:00" instead of "Idle" at print start
                job.setTimeStarted(1)
                job.setTime(datetime.now(), 2)
                job.updateTimeTracking()

                # Stream and execute G-code commands line-by-line
                for line in g:
                    # Check for cancellation request
                    if self.status == "cancelled":
                        self.sendGcode(self.cancelCMD)
                        self.verdict = "cancelled"
                        if self.logger:
                            self.logger.log("Job cancelled")
                        return True

                    # Color change support (future feature)
                    if "layer" in line.lower() and self.status == 'colorchange':
                        # TODO: implement color change handling
                        pass

                    # Track layer height for progress display
                    # Slicers insert ";LAYER_CHANGE" followed by ";Z:X.XX" to mark layer transitions
                    if prev_line and ";LAYER_CHANGE" in prev_line:
                        match = re.search(r";Z:(\d+\.?\d*)", line)
                        if match:
                            current_layer_height = float(match.group(1))
                            job.setCurrentLayerHeight(current_layer_height)
                    prev_line = line

                    # Clean up G-code line
                    line = line.strip()  # Remove leading/trailing whitespace
                    if ";" in line:  # Remove inline comments (everything after semicolon)
                        line = line.split(";")[0].strip()

                    # Skip empty lines and comment-only lines
                    if len(line) == 0 or line.startswith(";"):
                        continue

                    # Emit "Fabricating..." message when actual printing starts (M75 command)
                    if "M75" in line or self.startTimeCMD in line:
                        if current_app:
                            current_app.socketio.emit("console_update", {"message": "Fabricating...", "level": "info", "fabricator_id": self.dbID})

                    # Parse M73 progress/time commands (Prusa firmware)
                    # M73 provides real-time estimates directly from the printer firmware
                    # Format: M73 P<progress%> R<remaining_minutes> Q<progress_silent%> S<remaining_silent_minutes>
                    # This is more accurate than calculated estimates since printer knows actual speeds
                    if line.startswith("M73"):
                        # Parse all M73 parameters (re already imported at top of file)
                        p_match = re.search(r'P(\d+)', line)  # Normal mode progress percentage
                        r_match = re.search(r'R(\d+)', line)  # Normal mode remaining time (minutes)
                        q_match = re.search(r'Q(\d+)', line)  # Silent mode progress percentage
                        s_match = re.search(r'S(\d+)', line)  # Silent mode remaining time (minutes)

                        if p_match:
                            # Progress from printer overrides line-based calculation
                            printer_progress = int(p_match.group(1))
                            job.setProgress(float(printer_progress))

                        if r_match:
                            # Use normal mode remaining time
                            remaining_minutes = int(r_match.group(1))
                            job._printer_remaining_time = remaining_minutes * 60  # Convert to seconds

                        # For Prusa printers in silent mode, Q/S may be more accurate than P/R
                        # Use silent mode time if available and different from normal mode
                        if s_match:
                            remaining_silent_minutes = int(s_match.group(1))
                            # Prefer silent mode estimate if printer is in silent mode
                            job._printer_remaining_time = remaining_silent_minutes * 60

                        # Update time tracking display immediately when M73 received
                        if p_match or r_match or q_match or s_match:
                            job.updateTimeTracking()

                    # Send G-code command and check for errors
                    if not self.sendGcode(line, logger=self.logger):
                        error_msg = f"Failed to send G-code: {line.strip()}"
                        print(f"[Printer] {error_msg}")
                        if self.logger:
                            self.logger.error(error_msg)
                        self.verdict = "error"
                        return False

                    # Add line to buffer for live gcode preview
                    gcode_lines_buffer.append(line)

                    if job.getFilePause() == 1:
                        # self.setStatus("printing")
                        job.setTime(job.colorEta(), 1)
                        job.setTime(job.calculateColorChangeTotal(), 0)
                        job.setTime(datetime.min, 3)
                        job.setFilePause(0)
                        if self.status == "cancelled":
                            self.sendGcode(self.cancelCMD, logger=logger)
                            self.verdict = "cancelled"
                            logger.log("Job cancelled")
                            pass
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
                        pause_start = time()
                        pause_timeout = 3600.0  # 1 hour max pause
                        while self.status == "paused" and (time() - pause_start) < pause_timeout:
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
                                logger.log("Job cancelled")
                                pass
                                current_app.socketio.emit("console_update", {"message": "Job cancelled", "level": "info", "fabricator_id": self.dbID})
                                return True
                            elif self.status == "printing":
                                self.resume()
                                job.setTime(job.colorEta(), 1)
                                job.setTime(job.calculateColorChangeTotal(), 0)
                                job.setTime(datetime.min, 3)

                        # Check if we exited due to timeout
                        if self.status == "paused" and (time() - pause_start) >= pause_timeout:
                            print(f"[Printer] Pause timeout after {pause_timeout}s, resuming print")
                            logger.log(f"Pause timeout after {pause_timeout}s, resuming print")
                            current_app.socketio.emit("console_update", {"message": f"Pause timeout after {pause_timeout}s, resuming print", "level": "warning", "fabricator_id": self.dbID})
                            self.paused = False
                            self.status = "printing"
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

                    # Update time tracking (throttled to every 1% change to reduce socket traffic)
                    if int(progress) > last_progress_update:
                        last_progress_update = int(progress)
                        job.updateTimeTracking()

                        # Emit gcode preview update for live rendering (throttled with time tracking)
                        if gcode_lines_buffer and current_app:
                            current_app.socketio.emit('gcode_progress_update', {
                                'job_id': job.id,
                                'fabricator_id': self.dbID,
                                'line_number': sent_lines,
                                'total_lines': total_lines,
                                'progress': progress,
                                'current_layer_height': job.current_layer_height,
                                'gcode_chunk': '\n'.join(gcode_lines_buffer)
                            })
                            # Clear buffer after emission
                            gcode_lines_buffer = []

                    # if self.status == "complete" and job.extruded != 0:
                    if self.status == "complete":
                        self.verdict = "complete"
                        logger.log("Job complete")
                        pass
                        current_app.socketio.emit("console_update", {"message": "Job complete", "level": "info", "fabricator_id": self.dbID})
                        return True

                    if self.status == "error":
                        self.verdict = "error"
                        logger.error("Job error")
                        pass
                        current_app.socketio.emit("console_update", {"message": "Job error", "level": "error", "fabricator_id": self.dbID})
                        return True
            self.verdict = "complete"
            self.status = "complete"

            # Emit gcode complete event for live preview
            if current_app:
                current_app.socketio.emit('gcode_complete', {
                    'job_id': job.id,
                    'fabricator_id': self.dbID,
                    'gcode_complete': True
                })
            logger.log("Job complete")
            pass
            current_app.socketio.emit("console_update", {"message": "Job complete", "level": "info", "fabricator_id": self.dbID})
            return True
        except Exception as e:
            self.verdict = "error"
            print(f"[Printer] EXCEPTION in parseGcode: {e}")
            current_app.socketio.emit("error_update",{"fabricator_id": self.dbID, "job_id": job.id, "error": str(e)})
            current_app.socketio.emit("console_update", {"message": "Job error", "level": "error", "fabricator_id": self.dbID})
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)
            return False  # Return False not exception object
        finally:
            # Disable keepalive messages when print ends (success, error, or cancellation)
            self.disableKeepalive(logger=self.logger)

    def sendGcode(self, gcode: bytes | str, logger = None) -> bool:
        """
        Send a single G-code command to the printer and wait for response validation.

        This method implements a synchronous command/response protocol:
        1. Send G-code command via serial
        2. Read response lines until validator confirms success or timeout occurs
        3. Handle special cases like temperature monitoring and multi-line responses

        The method uses validator functions (from callablesHashtable) to determine
        when a command has completed successfully. For example:
        - checkOK: Waits for "ok" response
        - checkExtruderTemp: Waits for nozzle to reach target temperature
        - checkFirmware: Reads all M115 Cap: lines until "ok"

        :param bytes | str gcode: G-code command to send (automatically adds newline if missing)
        :param Logger logger: Optional logger instance for debug output
        :return: True if command succeeded, False if failed or timed out
        :rtype: bool

        :raises AssertionError: If serial connection is None or not open

        Timeout behavior:
            - Temperature commands (M109, M190): 20 minutes
            - Regular commands: 10 seconds
            - Cancellation: Returns True immediately if status is "cancelled"

        Notes:
            - Temperature lines (T:X B:Y format) are automatically parsed via handleTempLine()
            - Empty responses are silently skipped (keepalive may cause empty reads)
            - "echo:busy: processing" messages are filtered out
            - Debug output shows all sent commands and received responses
        """
        # Use provided logger or fall back to printer's logger
        if logger is None: logger = self.logger
        should_log = logger is not None

        # Validate serial connection is ready
        assert self.serialConnection is not None, "Serial connection is None"
        assert self.serialConnection.is_open, "Serial connection is not open"

        # Ensure command is properly formatted as bytes with newline
        if isinstance(gcode, str):
            if gcode[-1] != "\n": gcode += "\n"
            gcode = gcode.encode("utf-8")
        assert isinstance(gcode, bytes), f"Expected bytes, got {type(gcode)}"

        # Get validator functions for this command (defaults to checkOK)
        callables = self.callablesHashtable.get(self.extractIndex(gcode, logger), [checkOK])

        # Debug: Print command being sent
        print(f">>> SENDING GCODE: {gcode.decode().strip()}")

        # Write command to serial port
        self.serialConnection.write(gcode)
        line = b''

        # Set timeout based on command type
        gcode_str = gcode.decode().strip().split()[0]
        if gcode_str in ["M109", "M190"]:
            timeout_seconds = 1200.0  # 20 minutes for heating commands
        else:
            timeout_seconds = 10.0  # 10 seconds for regular commands

        # Process each validator function for this command
        for func in callables:
            # Reset timeout start time for each callable
            start_time = time()
            while True:
                if self.status == "cancelled": return True

                # Check if timeout has been reached using actual elapsed time
                elapsed_time = time() - start_time
                if elapsed_time >= timeout_seconds:
                    # Print timeout
                    print(f">>> TIMEOUT waiting for response to: {gcode.decode().strip()} after {elapsed_time:.2f}s")
                    if should_log: logger.warning(f"Timeout waiting for response to {gcode.decode().strip()} after {elapsed_time:.2f}s")
                    if gcode_str in ["M109", "M190"]:
                        if should_log: logger.log(f"Temperature command {gcode_str} timed out, assuming success")
                        break
                    break
                try:
                    line = self.serialConnection.readline()

                    #Empty line, continue
                    if not line:
                        print(f">>> EMPTY LINE from readline() - continuing")
                        continue

                    decLine = line.decode("utf-8").strip()

                    # If the line is empty after decoding, continue
                    if not decLine:
                        print(f">>> EMPTY DECODED LINE - continuing")
                        continue

                    # Print ALL responses received
                    print(f"<<< RECEIVED: {decLine}")

                    if "processing" in decLine or "echo" in decLine: continue
                    if "T:" in decLine and "B:" in decLine:
                        # Highlight temperature lines
                        print(f"<<< TEMPERATURE LINE: {decLine}")
                        self.handleTempLine(decLine)

                        if func == checkBedTemp and self.bedTemperature and self.bedTargetTemp:
                            print(f">>> CHECKING BED TEMP: Current={self.bedTemperature}°C, Target={self.bedTargetTemp}°C, Diff={abs(self.bedTemperature - self.bedTargetTemp)}")
                            if abs(self.bedTemperature - self.bedTargetTemp) <= 2:  # Within 2 degrees
                                # Print when bed temp reached
                                print(f"<<< BED TEMP REACHED: {self.bedTemperature}°C (target: {self.bedTargetTemp}°C)")
                                if should_log: logger.log(f"Bed temperature reached: {self.bedTemperature}°C")
                                break
                            else:
                                print(f">>> BED TEMP NOT REACHED YET: Need {self.bedTargetTemp - self.bedTemperature:.1f}°C more")
                        elif func == checkExtruderTemp and self.nozzleTemperature and self.nozzleTargetTemp:
                            if abs(self.nozzleTemperature - self.nozzleTargetTemp) <= 2:  # Within 2 degrees
                                # Print when nozzle temp reached
                                print(f"<<< NOZZLE TEMP REACHED: {self.nozzleTemperature}°C (target: {self.nozzleTargetTemp}°C)")
                                if should_log: logger.log(f"Nozzle temperature reached: {self.nozzleTemperature}°C")
                                break
                        elif func != checkBedTemp and func != checkExtruderTemp and "ok" not in decLine.lower():
                            continue
                        
                    # Special handling for M190, 'ok' as completion
                    gcode_str = gcode.decode().strip().split()[0]
                    if gcode_str == "M190" and "ok" in decLine.lower():
                        print(f"<<< M190 COMPLETED WITH OK: {decLine}")
                        break
                    
                    validator_result = func(line, self)
                    print(f">>> VALIDATOR {func.__name__} returned: {validator_result}")
                    if validator_result:
                        # Print when command completes successfully
                        print(f"<<< COMMAND COMPLETED: {gcode.decode().strip()} -> {decLine}")
                        break
                    if should_log: logger.debug(f"{gcode.decode().strip()}: {decLine}")
                    # current_app.socketio.emit("console_update",{"message": decLine, "level": "debug", "fabricator_id": self.dbID})
                except SerialTimeoutException as e:
                    if "no data" in str(e):
                        if should_log: logger.debug(f"No report temp line sent.")
                        self.serialConnection.write(b"M155 S1\n") # Convert to Bytes. Added a new line to ensure the command is sent correctly
                    else:
                        if current_app: return current_app.handle_errors_and_logging(e, logger)
                        else: print(traceback.format_exc())
                        return False
                except UnicodeDecodeError:
                    if should_log: logger.debug(f"{gcode.decode().strip()}: {line}")
                    else: print(f"{gcode.decode().strip()}: {line}")
                    # current_app.socketio.emit("console_update",{"message": gcode.decode().strip(), "level": "debug", "fabricator_id": self.dbID})
                except Exception as e:
                    if current_app: return current_app.handle_errors_and_logging(e, logger)
                    else: print(traceback.format_exc())
                    return False
        if not callables:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.decode().strip()}: ok", "level": "info", "fabricator_id": self.dbID})
            if should_log: logger.log(f"{gcode.decode().strip()}: ok")
        else:
            # current_app.socketio.emit("console_update", {"message": f"{gcode.decode().strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}", "level": "info", "fabricator_id": self.dbID})
            if should_log: logger.log(
                f"{gcode.decode().strip()}: {(line.decode() if isinstance(line, bytes) else line).strip()}")
        return True

    def changeFilament(self, filamentType: str, filamentDiameter: float, logger = None):
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

    def changeNozzle(self, nozzleDiameter: float, logger = None):
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

    def handleTempLine(self, line: str | bytes , logger = None) -> None:
        try:
            # Convert bytes to string if needed
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')

            # Print what we're parsing
            print(f">>> PARSING TEMP LINE: {line}")

            # Use regex to find the temperatures in the line (Ari's OG code)    
            temp_t = re.search(r'T:(\d+.\d+)', line)
            temp_b = re.search(r'B:(\d+.\d+)', line)
            if not temp_t:
                temp_t = re.search(r'T:(\d+)', line)
            if not temp_b:
                temp_b = re.search(r'B:(\d+)', line)
            if temp_t:
                self.nozzleTemperature = float(temp_t.group(1))
                print(f">>> PARSED NOZZLE TEMP: {self.nozzleTemperature}°C")
            if temp_b:
                self.bedTemperature = float(temp_b.group(1))
                print(f">>> PARSED BED TEMP: {self.bedTemperature}°C")
            if current_app:
                current_app.socketio.emit('temp_update', {'fabricator_id': self.dbID, 'extruder_temp': self.nozzleTemperature,
                                                          'bed_temp': self.bedTemperature})
                print(f">>> EMITTED TEMP UPDATE: Nozzle={self.nozzleTemperature}°C, Bed={self.bedTemperature}°C")
        except ValueError:
            pass
        except Exception as e:
            current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    # TODO: Do we need this? Can we just send raw gcode?
    def extractIndex(self, gcode: bytes, logger=None) -> str:
        """
        Method to extract the index of the gcode for use in the callablesHashtable
        :param bytes gcode: the line of gcode to extract the index from
        :param JobLogger | None logger: the logger to use
        :rtype: str
        """
        if logger is None: logger = self.logger
        hashIndex = gcode.decode().split("\n")[0].split(" ")[0]
        decGcode = gcode.decode()

        match hashIndex:
            case "M104":
                try:
                    temp = decGcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = decGcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    # Extract just the number part before converting to float
                    temp_str = temp.split()[0] if ' ' in temp else temp
                    self.nozzleTargetTemp = float(temp_str)
            case "M140":
                try:
                    temp = decGcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = decGcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    #  Apply same fix here
                    temp_str = temp.split()[0] if ' ' in temp else temp
                    self.bedTargetTemp = float(temp_str)
            case "M109":
                try:
                    temp = decGcode.split("S")[1].split("\n")[0]
                except IndexError:
                    try:
                        temp = decGcode.split("R")[1].split("\n")[0]
                    except IndexError:
                        temp = None
                if temp:
                    # Apply same fix here
                    temp_str = temp.split()[0] if ' ' in temp else temp
                    if logger is not None: logger.log(f"Waiting for hotend temperature to stabilize at {temp_str}\u00B0C...")
                    self.nozzleTargetTemp = float(temp_str)
                    current_app.socketio.emit("console_update",
                                          {"message": f"Waiting for hotend temperature to stabilize at {temp_str}\u00B0C...", "level": "info",
                                           "fabricator_id": self.dbID})
                else:
                    if logger is not None: logger.log("Waiting for hotend temperature to stabilize...")
                    current_app.socketio.emit("console_update",
                                          {"message": "Waiting for hotend temperature to stabilize...", "level": "info",
                                           "fabricator_id": self.dbID})
            case "M190":
                try:
                    temp = decGcode.split("S")[1].split("\n")[0]
                except IndexError:
                    temp = None
                if temp:
                    #  Apply same fix here
                    temp_str = temp.split()[0] if ' ' in temp else temp
                    if logger is not None: logger.log(f"Waiting for bed temperature to stabilize at {temp_str}\u00B0C...")
                    self.bedTargetTemp = float(temp_str)
                    current_app.socketio.emit("console_update",
                                          {"message": f"Waiting for bed temperature to stabilize at {temp_str}\u00B0C...", "level": "info",
                                           "fabricator_id": self.dbID})
                else:
                    if logger is not None: logger.log("Waiting for bed temperature to stabilize...")
                    current_app.socketio.emit("console_update",
                                          {"message": "Waiting for bed temperature to stabilize...", "level": "info",
                                           "fabricator_id": self.dbID})
            case "G28":
                if logger is not None: logger.log("Homing...")
                current_app.socketio.emit("console_update", {"message": "Homing...", "level": "info", "fabricator_id": self.dbID})
        return hashIndex

    def pause(self, logger = None):
        if not self.pauseCMD:
            if self.logger is not None: self.logger.error("Pause command not implemented.")
            return True
        try:
            assert self.pauseCMD is not None
            assert isinstance(self, Device)
            assert self.serialConnection is not None
            assert self.serialConnection.is_open
            if hasattr(self, "keepAliveCMD") and self.keepAliveCMD:
                self.enableKeepalive(logger=logger)
            self.sendGcode(self.pauseCMD)
            if self.logger is not None: self.logger.log("Job Paused")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def resume(self, logger = None) -> bool:
        if self.resumeCMD is None:
            if self.logger is not None: self.logger.error("Resume command not implemented.")
            return False
        try:
            assert isinstance(self, Device), "self is not an instance of Device"
            assert self.serialConnection is not None, "Serial connection is None"
            assert self.serialConnection.is_open, "Serial connection is not open"
            if hasattr(self, "doNotKeepAliveCMD") and self.doNotKeepAliveCMD:
                self.disableKeepalive(logger=logger)
            self.sendGcode(self.resumeCMD, False)
            if self.logger is not None: self.logger.log("Job Resumed")
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger if not logger else logger)

    def enableKeepalive(self, logger=None) -> bool:
        """
        Enable host keepalive messages to prevent serial timeout during long operations.

        Sends M113 S2 to enable keepalive messages every 2 seconds. This is essential
        during heating, bed leveling, and other operations that don't produce regular
        serial output.

        :param Logger logger: Optional logger instance
        :return: True if command succeeded, False otherwise
        :rtype: bool
        """
        try:
            print("[Printer] Enabling keepalive (M113 S2)")
            return self.sendGcode(self.keepAliveCMD, logger=logger)
        except Exception as e:
            print(f"[Printer] Failed to enable keepalive: {e}")
            if current_app:
                return current_app.handle_errors_and_logging(e, logger or self.logger)
            return False

    def disableKeepalive(self, logger=None) -> bool:
        """
        Disable host keepalive messages.

        Sends M113 S0 to stop keepalive messages. Should be called when disconnecting
        or when print job ends to prevent unnecessary serial traffic.

        :param Logger logger: Optional logger instance
        :return: True if command succeeded, False otherwise
        :rtype: bool
        """
        try:
            print("[Printer] Disabling keepalive (M113 S0)")
            return self.sendGcode(self.doNotKeepAliveCMD, logger=logger)
        except Exception as e:
            print(f"[Printer] Failed to disable keepalive: {e}")
            if current_app:
                return current_app.handle_errors_and_logging(e, logger or self.logger)
            return False

    def connect(self) -> bool:
        assert super().connect(), "Failed to connect to printer"
        try:
            assert self.serialConnection is not None, "Serial connection is None"
            assert self.serialConnection.is_open, "Serial connection is not open"
            # Enable auto temperature reporting (M155 S1 = 1 second interval)
            self.sendGcode("M155 S1\n", False)
            # Enable keepalive messages to prevent serial timeout during idle periods
            self.enableKeepalive(logger=self.logger)
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)

    def disconnect(self) -> bool:
        try:
            if self.serialConnection and self.serialConnection.is_open:
                # Disable keepalive messages before disconnecting
                self.disableKeepalive(logger=self.logger)
                # Disable temperature auto-reporting
                self.sendGcode("M155 S100\n", False)
                self.sendGcode("M155 S0\n", False)
                # Turn off heaters for safety
                self.sendGcode("M104 S0\n", False)
                self.sendGcode("M140 S0\n", False)
                # Disable motors
                self.sendGcode("M84\n", False)
                self.serialConnection.close()
            return True
        except Exception as e:
            return current_app.handle_errors_and_logging(e, self.logger)