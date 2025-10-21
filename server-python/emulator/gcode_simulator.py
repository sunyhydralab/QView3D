"""
G-code Simulator for Emulated Printer

Simulates realistic G-code command processing including:
- Movement commands (G0, G1, G28)
- Temperature control (M104, M140, M109, M190)
- Status reporting (M105, M114)
- Timing and delays
"""

import time
import re
from typing import Dict, Tuple, Optional

class GCodeSimulator:
    def __init__(self, config: Dict):
        self.config = config

        # Current state
        self.position = [0.0, 0.0, 0.0]  # X, Y, Z
        self.extruder_temp = 0.0
        self.bed_temp = 0.0
        self.target_extruder_temp = 0.0
        self.target_bed_temp = 0.0
        self.feedrate = 0.0

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
        """Handle M105 get temperature"""
        return f"ok T:{self.extruder_temp:.1f} /{self.target_extruder_temp:.1f} B:{self.bed_temp:.1f} /{self.target_bed_temp:.1f}"

    def _handle_get_position(self) -> str:
        """Handle M114 get current position"""
        return f"ok X:{self.position[0]:.2f} Y:{self.position[1]:.2f} Z:{self.position[2]:.2f}"

    def _handle_get_firmware_info(self) -> str:
        """Handle M115 get firmware version"""
        return "ok FIRMWARE_NAME:QView3D_Emulator FIRMWARE_VERSION:1.0.0 PROTOCOL_VERSION:1.0"

    def get_state(self) -> Dict:
        """Get current simulator state"""
        self.update_temperatures()
        return {
            'position': self.position.copy(),
            'extruder_temp': round(self.extruder_temp, 1),
            'bed_temp': round(self.bed_temp, 1),
            'target_extruder_temp': round(self.target_extruder_temp, 1),
            'target_bed_temp': round(self.target_bed_temp, 1),
            'feedrate': self.feedrate,
            'is_homed': self.is_homed
        }
