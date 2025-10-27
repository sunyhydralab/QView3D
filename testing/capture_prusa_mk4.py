#!/usr/bin/env python3
"""
Prusa MK4 Device Capture Script
Captures all gcode commands and responses for creating a realistic test emulator
"""

import serial
import serial.tools.list_ports
import time
import json
import sys
from datetime import datetime
from typing import List, Dict, Tuple


class PrusaMK4Capture:
    """Captures communication with Prusa MK4 printer"""

    def __init__(self, port: str = None, baudrate: int = 115200, timeout: float = 10.0):
        """
        Initialize capture session

        Args:
            port: Serial port (e.g., '/dev/ttyUSB0' or 'COM3')
            baudrate: Baud rate (default 115200 for Prusa MK4)
            timeout: Response timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.capture_log: List[Dict] = []
        self.session_start = datetime.now().isoformat()

    def list_available_ports(self) -> List[str]:
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        available = []
        print("\n=== Available Serial Ports ===")
        for port in ports:
            print(f"  {port.device}")
            print(f"    Description: {port.description}")
            print(f"    Manufacturer: {port.manufacturer}")
            available.append(port.device)
        print()
        return available

    def connect(self) -> bool:
        """Connect to the printer"""
        if not self.port:
            ports = self.list_available_ports()
            if not ports:
                print("ERROR: No serial ports found!")
                return False

            print("Enter port name (or press Enter for first available):")
            user_port = input().strip()
            self.port = user_port if user_port else ports[0]

        try:
            print(f"Connecting to {self.port} at {self.baudrate} baud...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout
            )

            # Wait for printer to initialize
            print("Waiting for printer to initialize...")
            time.sleep(2)

            # Read any startup messages
            startup_messages = []
            while self.serial_connection.in_waiting:
                line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    startup_messages.append(line)
                    print(f"  << {line}")

            if startup_messages:
                self.capture_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "startup",
                    "messages": startup_messages
                })

            print(f"Connected successfully to {self.port}\n")
            return True

        except serial.SerialException as e:
            print(f"ERROR: Failed to connect: {e}")
            return False

    def send_gcode(self, command: str, wait_for_ok: bool = True,
                   additional_responses: int = 0, response_timeout: float = None) -> Tuple[List[str], float]:
        """
        Send a gcode command and capture the response

        Args:
            command: The gcode command to send
            wait_for_ok: Wait for 'ok' response
            additional_responses: Number of additional response lines to read after 'ok'
            response_timeout: Override default timeout for this command

        Returns:
            Tuple of (response_lines, duration_seconds)
        """
        if not self.serial_connection:
            raise Exception("Not connected to printer")

        # Clean command
        command = command.strip()
        if not command:
            return ([], 0.0)

        # Send command
        start_time = time.time()
        print(f"  >> {command}")
        self.serial_connection.write(f"{command}\n".encode('utf-8'))
        self.serial_connection.flush()

        # Read responses
        responses = []
        timeout = response_timeout if response_timeout else self.timeout
        end_time = start_time + timeout

        while time.time() < end_time:
            if self.serial_connection.in_waiting:
                try:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        responses.append(line)
                        print(f"  << {line}")

                        # Check if we got 'ok' and should stop
                        if wait_for_ok and line.lower().startswith('ok'):
                            # Read any additional responses
                            for _ in range(additional_responses):
                                time.sleep(0.1)
                                if self.serial_connection.in_waiting:
                                    extra_line = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                                    if extra_line:
                                        responses.append(extra_line)
                                        print(f"  << {extra_line}")
                            break
                except UnicodeDecodeError:
                    print("  << [Binary data received]")
                    responses.append("[BINARY_DATA]")
            else:
                time.sleep(0.01)

        duration = time.time() - start_time

        # Log the exchange
        self.capture_log.append({
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "responses": responses,
            "duration_seconds": round(duration, 3),
            "wait_for_ok": wait_for_ok,
            "completed": any('ok' in r.lower() for r in responses) if wait_for_ok else True
        })

        return (responses, duration)

    def run_test_sequence(self):
        """Run comprehensive test sequence for Prusa MK4"""
        print("\n" + "="*60)
        print("Starting Prusa MK4 Test Sequence")
        print("="*60 + "\n")

        test_commands = [
            # Firmware and device info
            ("M115", "Get firmware info", True, 5),

            # Temperature commands
            ("M105", "Get temperatures", True, 2),
            ("M104 S0", "Set extruder temp to 0", True, 0),
            ("M140 S0", "Set bed temp to 0", True, 0),

            # Position and endstops
            ("M114", "Get current position", True, 5),
            ("M119", "Get endstop status", True, 5),

            # Movement (be careful - only small movements!)
            ("G91", "Set relative positioning", True, 0),
            ("G1 Z5 F100", "Move Z up 5mm slowly", True, 0),
            ("G1 Z-5 F100", "Move Z down 5mm", True, 0),
            ("G90", "Set absolute positioning", True, 0),

            # Printer state
            ("M503", "Get current settings", True, 30, 30.0),  # Can be long response
            ("M220", "Get/Set speed factor", True, 1),
            ("M221", "Get/Set flow rate", True, 1),

            # Fan control
            ("M106 S0", "Turn off fan", True, 0),
            ("M107", "Turn off fan (alternative)", True, 0),

            # SD Card (if present)
            ("M21", "Initialize SD card", True, 1),
            ("M20", "List SD card files", True, 10, 15.0),

            # Prusa-specific commands
            ("M862.1 P\"MK4\"", "Check printer model", True, 1),
            ("M862.3 P\"[printer model name]\"", "Get printer name", True, 1),

            # Status and diagnostics
            ("M115 U3.13.2", "Report capabilities", True, 5),

            # Final temperature check
            ("M105", "Final temperature check", True, 2),
        ]

        print("Will execute the following test commands:")
        for i, (cmd, desc, _, _, *_) in enumerate(test_commands, 1):
            print(f"  {i}. {desc}: {cmd}")

        print("\nWARNING: This will send commands to your printer!")
        print("Make sure your printer is ready and nothing is in the way.")
        print("\nPress Enter to continue or Ctrl+C to cancel...")
        input()

        # Execute each command
        for i, command_data in enumerate(test_commands, 1):
            cmd = command_data[0]
            desc = command_data[1]
            wait_ok = command_data[2]
            additional = command_data[3]
            custom_timeout = command_data[4] if len(command_data) > 4 else None

            print(f"\n[{i}/{len(test_commands)}] {desc}")
            print("-" * 60)

            try:
                responses, duration = self.send_gcode(
                    cmd,
                    wait_for_ok=wait_ok,
                    additional_responses=additional,
                    response_timeout=custom_timeout
                )

                if not responses:
                    print("  WARNING: No response received!")

                # Small delay between commands
                time.sleep(0.5)

            except Exception as e:
                print(f"  ERROR: {e}")
                self.capture_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "command": cmd,
                    "error": str(e)
                })

        print("\n" + "="*60)
        print("Test sequence completed!")
        print("="*60 + "\n")

    def save_capture(self, filename: str = None):
        """Save captured data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prusa_mk4_capture_{timestamp}.json"

        capture_data = {
            "device": "Prusa MK4",
            "session_start": self.session_start,
            "session_end": datetime.now().isoformat(),
            "port": self.port,
            "baudrate": self.baudrate,
            "total_commands": len([log for log in self.capture_log if log.get("type") != "startup"]),
            "capture_log": self.capture_log
        }

        with open(filename, 'w') as f:
            json.dump(capture_data, f, indent=2)

        print(f"\nCapture saved to: {filename}")
        print(f"  Total commands captured: {capture_data['total_commands']}")
        print(f"  Total log entries: {len(self.capture_log)}")

        return filename

    def disconnect(self):
        """Disconnect from printer"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            print("Disconnected from printer")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


def main():
    """Main execution"""
    print("""
==============================================================
         Prusa MK4 Device Capture Tool
  Captures gcode commands and responses for emulation
==============================================================
    """)

    # Parse command line arguments
    port = sys.argv[1] if len(sys.argv) > 1 else None
    baudrate = int(sys.argv[2]) if len(sys.argv) > 2 else 115200

    # Create capture session
    with PrusaMK4Capture(port=port, baudrate=baudrate) as capture:
        # Connect to printer
        if not capture.connect():
            print("Failed to connect. Exiting.")
            return 1

        try:
            # Run test sequence
            capture.run_test_sequence()

            # Save results
            filename = capture.save_capture()

            print(f"\n{'='*60}")
            print("Next Steps:")
            print(f"{'='*60}")
            print(f"1. Review the captured data in: {filename}")
            print(f"2. Use this data to enhance the emulator at:")
            print(f"   server-python/emulator/gcode_simulator.py")
            print(f"3. Update emulator responses to match real Prusa MK4")
            print()

            return 0

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Saving partial capture...")
            capture.save_capture()
            return 1

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            capture.save_capture()
            return 1


if __name__ == "__main__":
    sys.exit(main())
