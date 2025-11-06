"""
G-code Simulator for Emulated Printer

Simulates realistic G-code command processing including:
- Movement commands (G0, G1, G28)
- Temperature control (M104, M140, M109, M190)
- Status reporting (M105, M114, M115, M119)
- Configuration (M503, M220, M221, M862)
- SD card operations (M20, M21)
- Timing and delays

Responses based on real Prusa MK4 capture data.
"""

import time
import re
from typing import Dict, Tuple, Optional, List

class GCodeSimulator:
    def __init__(self, config: Dict):
        self.config = config

        # Current state
        self.position = [-1.0, -4.0, 0.0]  # X, Y, Z (Prusa MK4 default unhomed position)
        self.position_count = [-100, -400, 0]  # Stepper counts
        self.extruder_temp = 25.0  # Room temperature
        self.bed_temp = 23.0  # Room temperature
        self.heatbreak_temp = 23.77  # X sensor in Prusa terminology
        self.board_temp = 35.64  # A sensor (ambient/board temp)
        self.target_extruder_temp = 0.0
        self.target_bed_temp = 0.0
        self.target_heatbreak_temp = 36.0
        self.feedrate = 0.0
        self.flow_percentage = 100  # E0 Flow percentage

        # Heating simulation
        self.heating_rate_extruder = config.get('simulation', {}).get('heating_rate_extruder', 2.5)
        self.heating_rate_bed = config.get('simulation', {}).get('heating_rate_bed', 1.5)
        self.cooling_rate = config.get('simulation', {}).get('cooling_rate', 0.8)

        # Limits from config
        printer_config = config.get('emulator', {}).get('default_printers', [{}])[0]
        self.build_volume = printer_config.get('build_volume', [250, 210, 220])
        self.max_temp_extruder = printer_config.get('max_temp_extruder', 300)
        self.max_temp_bed = printer_config.get('max_temp_bed', 120)
        self.max_feedrate = printer_config.get('max_feedrate', 200)

        # State flags
        self.is_homed = False
        self.last_update_time = time.time()

    def update_temperatures(self):
        """Update temperatures based on heating/cooling rates"""
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        # Update extruder temperature
        if self.extruder_temp < self.target_extruder_temp:
            self.extruder_temp += self.heating_rate_extruder * delta_time
            self.extruder_temp = min(self.extruder_temp, self.target_extruder_temp)
        elif self.extruder_temp > self.target_extruder_temp:
            self.extruder_temp -= self.cooling_rate * delta_time
            self.extruder_temp = max(self.extruder_temp, self.target_extruder_temp)

        # Update bed temperature
        if self.bed_temp < self.target_bed_temp:
            self.bed_temp += self.heating_rate_bed * delta_time
            self.bed_temp = min(self.bed_temp, self.target_bed_temp)
        elif self.bed_temp > self.target_bed_temp:
            self.bed_temp -= self.cooling_rate * delta_time
            self.bed_temp = max(self.bed_temp, self.target_bed_temp)

    def process_command(self, gcode: str) -> Tuple[str, float]:
        """
        Process a G-code command and return response and delay

        Returns:
            Tuple[str, float]: (response message, delay in seconds)
        """
        gcode = gcode.strip()
        if not gcode or gcode.startswith(';'):
            return "ok", 0.0

        # Update temperatures before processing
        self.update_temperatures()

        # Extract command
        parts = gcode.split()
        if not parts:
            return "ok", 0.0

        command = parts[0].upper()

        # G-codes (movement)
        if command == 'G0' or command == 'G1':  # Move
            return self._handle_move(gcode), 0.1

        elif command == 'G28':  # Home
            return self._handle_home(gcode), 2.0  # Homing takes time

        elif command == 'G90':  # Absolute positioning
            return "ok", 0.0

        elif command == 'G91':  # Relative positioning
            return "ok", 0.0

        elif command == 'G92':  # Set position
            return self._handle_set_position(gcode), 0.0

        # M-codes (control)
        elif command == 'M104':  # Set extruder temperature
            return self._handle_set_extruder_temp(gcode), 0.0

        elif command == 'M140':  # Set bed temperature
            return self._handle_set_bed_temp(gcode), 0.0

        elif command == 'M109':  # Set extruder temp and wait
            response = self._handle_set_extruder_temp(gcode)
            wait_time = abs(self.target_extruder_temp - self.extruder_temp) / self.heating_rate_extruder
            return response, wait_time

        elif command == 'M190':  # Set bed temp and wait
            response = self._handle_set_bed_temp(gcode)
            wait_time = abs(self.target_bed_temp - self.bed_temp) / self.heating_rate_bed
            return response, wait_time

        elif command == 'M105':  # Get temperature
            return self._handle_get_temperature(), 0.0

        elif command == 'M114':  # Get current position
            return self._handle_get_position(), 0.0

        elif command == 'M115':  # Get firmware info
            return self._handle_get_firmware_info(), 0.0

        elif command == 'M119':  # Get endstop status
            return self._handle_get_endstops(), 0.0

        elif command == 'M503':  # Get configuration
            return self._handle_get_config(), 3.0  # Takes time to send all config

        elif command == 'M220':  # Get/Set speed percentage
            return "ok", 0.0

        elif command == 'M221':  # Get/Set flow percentage
            return self._handle_flow_percentage(), 0.0

        elif command == 'M106' or command == 'M107':  # Fan control
            return "ok", 0.0

        elif command == 'M20':  # List SD card
            return self._handle_list_sd(), 1.0  # Takes time to read SD

        elif command == 'M21':  # Initialize SD card
            return "ok", 0.0

        elif command.startswith('M862'):  # Prusa-specific model check
            return "ok", 0.0

        elif command == 'M555':  # Prusa-specific area definition
            return "ok", 0.0

        elif command.startswith('M73'):  # Set print progress
            return "ok", 0.0

        elif command.startswith('M155'):  # Temperature auto-report interval
            return "ok", 0.0

        elif command.startswith('M201'):  # Set max acceleration
            return "ok", 0.0

        elif command.startswith('M203'):  # Set max feedrate
            return "ok", 0.0

        elif command.startswith('M204'):  # Set acceleration
            return "ok", 0.0

        elif command.startswith('M205'):  # Advanced settings
            return "ok", 0.0

        elif command.startswith('M17'):  # Enable steppers
            return "ok", 0.0

        elif command.startswith('M486'):  # Cancel object
            return "ok", 0.0

        else:
            # Unknown command - just return ok
            return "ok", 0.0

    def _handle_move(self, gcode: str) -> str:
        """Handle G0/G1 movement commands"""
        # Extract coordinates
        x_match = re.search(r'X([-\d.]+)', gcode, re.IGNORECASE)
        y_match = re.search(r'Y([-\d.]+)', gcode, re.IGNORECASE)
        z_match = re.search(r'Z([-\d.]+)', gcode, re.IGNORECASE)
        f_match = re.search(r'F([-\d.]+)', gcode, re.IGNORECASE)

        if x_match:
            self.position[0] = float(x_match.group(1))
        if y_match:
            self.position[1] = float(y_match.group(1))
        if z_match:
            self.position[2] = float(z_match.group(1))
        if f_match:
            self.feedrate = float(f_match.group(1))

        return "ok"

    def _handle_home(self, gcode: str) -> str:
        """Handle G28 homing command"""
        # Check for specific axes
        if 'X' in gcode.upper():
            self.position[0] = 0.0
        if 'Y' in gcode.upper():
            self.position[1] = 0.0
        if 'Z' in gcode.upper():
            self.position[2] = 0.0

        # If no axes specified, home all
        if not any(axis in gcode.upper() for axis in ['X', 'Y', 'Z']):
            self.position = [0.0, 0.0, 0.0]

        self.is_homed = True
        return "ok"

    def _handle_set_position(self, gcode: str) -> str:
        """Handle G92 set position command"""
        x_match = re.search(r'X([-\d.]+)', gcode, re.IGNORECASE)
        y_match = re.search(r'Y([-\d.]+)', gcode, re.IGNORECASE)
        z_match = re.search(r'Z([-\d.]+)', gcode, re.IGNORECASE)

        if x_match:
            self.position[0] = float(x_match.group(1))
        if y_match:
            self.position[1] = float(y_match.group(1))
        if z_match:
            self.position[2] = float(z_match.group(1))

        return "ok"

    def _handle_set_extruder_temp(self, gcode: str) -> str:
        """Handle M104/M109 set extruder temperature"""
        s_match = re.search(r'S([-\d.]+)', gcode, re.IGNORECASE)
        if s_match:
            temp = float(s_match.group(1))
            self.target_extruder_temp = min(temp, self.max_temp_extruder)
        return "ok"

    def _handle_set_bed_temp(self, gcode: str) -> str:
        """Handle M140/M190 set bed temperature"""
        s_match = re.search(r'S([-\d.]+)', gcode, re.IGNORECASE)
        if s_match:
            temp = float(s_match.group(1))
            self.target_bed_temp = min(temp, self.max_temp_bed)
        return "ok"

    def _handle_get_temperature(self) -> str:
        """Handle M105 get temperature - Prusa MK4 format"""
        # Format: ok T:extruder/target B:bed/target X:heatbreak/target A:board/target @:extruder_power B@:bed_power HBR@:heatbreak_power
        extruder_power = 127 if self.extruder_temp < self.target_extruder_temp else 0
        bed_power = 127 if self.bed_temp < self.target_bed_temp else 0

        return (f"ok T:{self.extruder_temp:.2f}/{self.target_extruder_temp:.2f} "
                f"B:{self.bed_temp:.2f}/{self.target_bed_temp:.2f} "
                f"X:{self.heatbreak_temp:.2f}/{self.target_heatbreak_temp:.2f} "
                f"A:{self.board_temp:.2f}/0.00 "
                f"@:{extruder_power} B@:{bed_power} HBR@:0")

    def _handle_get_position(self) -> str:
        """Handle M114 get current position - Prusa MK4 format"""
        # Format includes both position and stepper counts
        response = f"X:{self.position[0]:.2f} Y:{self.position[1]:.2f} Z:{self.position[2]:.2f} E:0.00 Count X:{self.position_count[0]} Y:{self.position_count[1]} Z:{self.position_count[2]}\nok"
        return response

    def _handle_get_firmware_info(self) -> str:
        """Handle M115 get firmware version - Prusa MK4 format"""
        lines = [
            "FIRMWARE_NAME:Prusa-Firmware-Buddy 6.1.3+7898 (Github) SOURCE_CODE_URL:https://github.com/prusa3d/Prusa-Firmware-Buddy PROTOCOL_VERSION:1.0 MACHINE_TYPE:Prusa-MK4 EXTRUDER_COUNT:1 UUID:cede2a2f-41a2-4748-9b12-c55c62f367ff",
            "Cap:SERIAL_XON_XOFF:0",
            "Cap:BINARY_FILE_TRANSFER:0",
            "Cap:EEPROM:0",
            "Cap:VOLUMETRIC:1",
            "Cap:AUTOREPORT_TEMP:1",
            "Cap:PROGRESS:0",
            "Cap:PRINT_JOB:1",
            "Cap:AUTOLEVEL:1",
            "Cap:Z_PROBE:1",
            "Cap:LEVELING_DATA:1",
            "Cap:BUILD_PERCENT:0",
            "Cap:SOFTWARE_POWER:1",
            "Cap:TOGGLE_LIGHTS:0",
            "Cap:CASE_LIGHT_BRIGHTNESS:0",
            "Cap:EMERGENCY_PARSER:0",
            "Cap:PROMPT_SUPPORT:0",
            "Cap:AUTOREPORT_SD_STATUS:0",
            "Cap:THERMAL_PROTECTION:1",
            "Cap:MOTION_MODES:0",
            "Cap:CHAMBER_TEMPERATURE:0",
            "ok"
        ]
        return "\n".join(lines)

    def _handle_get_endstops(self) -> str:
        """Handle M119 get endstop status - Prusa MK4 format"""
        lines = [
            "Reporting endstop status",
            "x_min: open",
            "x_max: open",
            "y_min: open",
            "y_max: open",
            "z_min: open",
            "z_max: open",
            "ok"
        ]
        return "\n".join(lines)

    def _handle_flow_percentage(self) -> str:
        """Handle M221 get/set flow percentage - Prusa MK4 format"""
        return f"echo:E0 Flow: {self.flow_percentage}%\nok"

    def _handle_list_sd(self) -> str:
        """Handle M20 list SD card files - Prusa MK4 format"""
        lines = [
            "Begin file list",
            "TEST_P~1.GCO",
            "SAMPLE~1.BGC",
            "DEMO_F~1.GCO",
            "End file list",
            "ok"
        ]
        return "\n".join(lines)

    def _handle_get_config(self) -> str:
        """Handle M503 get configuration - Prusa MK4 format"""
        lines = [
            "echo:  G21    ; Units in mm (mm)",
            "echo:Filament settings: Disabled",
            "echo:  M200 D1.75",
            "echo:  M200 D0",
            "echo:Steps per unit:",
            "echo: M92 X100.00 Y100.00 Z400.00 E380.00",
            "echo:Maximum feedrates (units/s):",
            "echo:  M203 X300.00 Y300.00 Z40.00 E50.00",
            "echo:Maximum Acceleration (units/s2):",
            "echo:  M201 X1250.00 Y1250.00 Z200.00 E1500.00",
            "echo:Acceleration (units/s2): P<print_accel> R<retract_accel> T<travel_accel>",
            "echo:  M204 P1250.00 R800.00 T1250.00",
            "echo:Advanced: B<min_segment_time_us> S<min_feedrate> T<min_travel_feedrate> X<max_x_jerk> Y<max_y_jerk> Z<max_z_jerk> E<max_e_jerk>",
            "echo:  M205 B20000.00 S0.00 T0.00 X8.00 Y8.00 Z2.00 E5.00",
            "echo:Home offset:",
            "echo:  M206 X0.00 Y0.00 Z0.00",
            "echo:Unified Bed Leveling:",
            "echo:  M420 S0 Z0.00",
            "Unified Bed Leveling System v1.01 inactive",
            "echo:PID settings:",
            "echo:  M301 P14.00 I1.00 D100.00",
            "echo:  M304 P126.13 I4.30 D924.76",
            "echo:Z-Probe Offset (mm):",
            "echo:  M851 X0.00 Y0.00 Z0.00",
            "ok"
        ]
        return "\n".join(lines)

    def get_state(self) -> Dict:
        """Get current simulator state"""
        self.update_temperatures()
        return {
            'position': self.position.copy(),
            'position_count': self.position_count.copy(),
            'extruder_temp': round(self.extruder_temp, 2),
            'bed_temp': round(self.bed_temp, 2),
            'heatbreak_temp': round(self.heatbreak_temp, 2),
            'board_temp': round(self.board_temp, 2),
            'target_extruder_temp': round(self.target_extruder_temp, 2),
            'target_bed_temp': round(self.target_bed_temp, 2),
            'feedrate': self.feedrate,
            'is_homed': self.is_homed,
            'flow_percentage': self.flow_percentage
        }
