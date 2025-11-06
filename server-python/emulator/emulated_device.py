"""
Emulated Device Class

Represents a virtual 3D printer with realistic behavior simulation.
"""

import random
import string
from typing import Dict, Optional
from .gcode_simulator import GCodeSimulator

class EmulatedDevice:
    def __init__(self, config: Dict, name: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize an emulated printer device

        Args:
            config: Configuration dictionary from emulator_config.json
            name: Custom name for the printer
            model: Printer model name
        """
        # Get default printer config
        default_config = config.get('emulator', {}).get('default_printers', [{}])[0]

        # Device identification
        self.name = name or default_config.get('name', 'Emulated Printer')
        self.model = model or default_config.get('model', 'Generic 3D Printer')
        self.hwid = self._generate_hwid()
        self.port = f"EMU_{self.hwid}"

        # Device specifications
        self.build_volume = default_config.get('build_volume', [250, 210, 220])
        self.max_temp_extruder = default_config.get('max_temp_extruder', 300)
        self.max_temp_bed = default_config.get('max_temp_bed', 120)
        self.max_feedrate = default_config.get('max_feedrate', 200)

        # Initialize G-code simulator
        self.simulator = GCodeSimulator(config)

        # Device state
        self.status = 'idle'  # idle, printing, paused, error
        self.is_connected = False
        self.error_message = None

    def _generate_hwid(self) -> str:
        """Generate a unique hardware ID for this emulated device"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def connect(self) -> bool:
        """Simulate device connection"""
        self.is_connected = True
        self.status = 'idle'
        return True

    def disconnect(self) -> bool:
        """Simulate device disconnection"""
        self.is_connected = False
        self.status = 'offline'
        return True

    def send_command(self, gcode: str) -> tuple[str, float]:
        """
        Send a G-code command to the emulated device

        Args:
            gcode: G-code command string

        Returns:
            Tuple of (response, delay_seconds)
        """
        if not self.is_connected:
            return "Error: Device not connected", 0.0

        try:
            response, delay = self.simulator.process_command(gcode)
            return response, delay
        except Exception as e:
            self.status = 'error'
            self.error_message = str(e)
            return f"Error: {str(e)}", 0.0

    def get_state(self) -> Dict:
        """Get current device state"""
        simulator_state = self.simulator.get_state()

        return {
            'name': self.name,
            'model': self.model,
            'hwid': self.hwid,
            'port': self.port,
            'status': self.status,
            'is_connected': self.is_connected,
            'error_message': self.error_message,
            'build_volume': self.build_volume,
            'max_temp_extruder': self.max_temp_extruder,
            'max_temp_bed': self.max_temp_bed,
            **simulator_state
        }

    def start_printing(self) -> bool:
        """Simulate starting a print job"""
        if not self.is_connected:
            return False

        self.status = 'printing'
        return True

    def pause_printing(self) -> bool:
        """Simulate pausing a print job"""
        if self.status != 'printing':
            return False

        self.status = 'paused'
        return True

    def resume_printing(self) -> bool:
        """Simulate resuming a print job"""
        if self.status != 'paused':
            return False

        self.status = 'printing'
        return True

    def cancel_printing(self) -> bool:
        """Simulate canceling a print job"""
        if self.status not in ['printing', 'paused']:
            return False

        self.status = 'idle'
        return True

    def to_dict(self) -> Dict:
        """Convert device to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'model': self.model,
            'hwid': self.hwid,
            'port': self.port,
            'status': self.status,
            'is_connected': self.is_connected,
            'build_volume': self.build_volume
        }
