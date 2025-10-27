# Prusa MK4 Capture Tool

This script captures real gcode commands and responses from your Prusa MK4 3D printer to create a realistic test emulator.

## Installation

```bash
pip install -r capture_requirements.txt
```

## Usage

### Auto-detect Serial Port

```bash
python capture_prusa_mk4.py
```

The script will list available serial ports and let you choose.

### Specify Serial Port

```bash
# Linux/Mac
python capture_prusa_mk4.py /dev/ttyUSB0

# Windows
python capture_prusa_mk4.py COM3
```

### Custom Baud Rate

```bash
python capture_prusa_mk4.py /dev/ttyUSB0 115200
```

## What It Does

The script will:

1. **Connect** to your Prusa MK4 via serial
2. **Capture** startup messages
3. **Send test commands** including:
   - Firmware info (M115)
   - Temperature queries (M105)
   - Position requests (M114)
   - Endstop status (M119)
   - Settings dump (M503)
   - Prusa-specific commands (M862.x)
   - Small test movements (safe Z-axis movements)
4. **Log all responses** with timestamps and durations
5. **Save to JSON** file with format: `prusa_mk4_capture_YYYYMMDD_HHMMSS.json`

## Safety Notes

- The script performs minimal movements (only 5mm Z-axis)
- Ensure your printer is in a safe state before running
- Make sure nothing is blocking Z-axis movement
- You can press Ctrl+C to stop at any time

## Test Commands Included

| Command | Description | Notes |
|---------|-------------|-------|
| M115 | Firmware info | Identifies printer model and firmware |
| M105 | Get temperatures | Current temps and targets |
| M104 S0 | Set extruder temp | Sets to 0°C for safety |
| M140 S0 | Set bed temp | Sets to 0°C for safety |
| M114 | Get position | Current X/Y/Z/E coordinates |
| M119 | Endstop status | Whether endstops are triggered |
| G91/G90 | Positioning mode | Relative vs absolute |
| G1 Z5/Z-5 | Test movement | Small Z movements only |
| M503 | Get settings | Extensive settings dump |
| M220 | Speed factor | Current speed multiplier |
| M221 | Flow rate | Current flow percentage |
| M21/M20 | SD card | Initialize and list files |
| M862.x | Prusa-specific | Model checks |

## Output Format

The JSON output contains:

```json
{
  "device": "Prusa MK4",
  "session_start": "2025-01-15T10:30:00",
  "session_end": "2025-01-15T10:35:00",
  "port": "/dev/ttyUSB0",
  "baudrate": 115200,
  "total_commands": 20,
  "capture_log": [
    {
      "timestamp": "2025-01-15T10:30:05",
      "command": "M115",
      "responses": [
        "FIRMWARE_NAME:Prusa-Firmware ...",
        "ok"
      ],
      "duration_seconds": 0.234,
      "wait_for_ok": true,
      "completed": true
    }
  ]
}
```

## Using the Captured Data

After capturing, you can:

1. **Review responses** to understand your printer's behavior
2. **Update the emulator** at `server-python/emulator/gcode_simulator.py`
3. **Match real responses** for more realistic testing
4. **Create test cases** based on actual printer behavior

## Troubleshooting

### Permission Denied (Linux/Mac)

```bash
sudo usermod -a -G dialout $USER
# Then log out and back in
```

Or run with sudo:
```bash
sudo python capture_prusa_mk4.py /dev/ttyUSB0
```

### Port Not Found

- Check USB connection
- Try different USB port
- Check `ls /dev/tty*` (Linux/Mac) or Device Manager (Windows)

### No Response

- Verify baud rate (115200 for MK4)
- Check printer is powered on and not in error state
- Try resetting the printer
- Increase timeout in script if needed

### Partial Responses

- Some commands (like M503) return many lines - this is normal
- The script captures up to the timeout period

## Customization

Edit the `test_commands` list in `run_test_sequence()` to:

- Add more commands
- Remove commands you don't want
- Adjust timeouts for slow commands
- Add heating tests (be careful with temps!)

## Example: Add Custom Command

```python
("M117 Test", "Display message on screen", True, 0),
```

Format: `(command, description, wait_for_ok, additional_response_lines, optional_timeout)`
