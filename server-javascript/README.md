# QView3D JavaScript Components

## Virtual Printer Emulator

JavaScript-based 3D printer emulator that replaces the Go implementation. Connects to Python backend via WebSocket.

### Quick Start

```bash
cd server-javascript
npm install
npm run emulator
```

### Usage

```bash
# Default (Prusa MK4 on EMU0)
npm run emulator

# Specify model and port
node src/emulator/start_emulator.js PrusaMK4 EMU0

# Custom WebSocket URL
node src/emulator/start_emulator.js PrusaMK4 EMU0 ws://localhost:8001
```

### Supported Models

- `PrusaMK4` - Prusa i3 MK4
- `PrusaMK3` - Prusa i3 MK3
- `Ender3` - Creality Ender 3

### G-code Support

**Movement:**
- `G0/G1` - Linear movement (X, Y, Z, E axes)
- `G28` - Home axes

**Temperature:**
- `M104` - Set hotend temperature
- `M109` - Set hotend temperature and wait
- `M140` - Set bed temperature
- `M190` - Set bed temperature and wait
- `M105` - Get current temperatures

**Info:**
- `M115` - Get firmware info
- `M114` - Get current position

**Fan:**
- `M106` - Set fan speed
- `M107` - Turn fan off

**Debug:**
- `M118` - Echo message

### Architecture

```
┌─────────────────────┐
│  Python Backend     │
│  (port 8000)        │
└──────────┬──────────┘
           │
           │ WebSocket (port 8001)
           │
           ▼
┌─────────────────────┐
│  VirtualPrinter.js  │
│  - Process G-code   │
│  - Simulate state   │
│  - Send responses   │
└─────────────────────┘
```

### Connection Flow

1. Emulator connects to WebSocket server
2. Sends handshake with port/name/hwid
3. Python backend registers emulator as fabricator
4. Backend sends G-code commands
5. Emulator processes and responds
6. Frontend displays emulator in printer list

### State Simulation

The emulator maintains realistic printer state:

- **Position**: X, Y, Z, E coordinates updated by movement commands
- **Temperature**: Gradual heating simulation toward target temps
- **Homing**: Simulated homing delay
- **Fan**: Speed tracking

### Development

```bash
# Test emulator connection
npm run emulator

# In another terminal, start Python backend
cd ../
python3 run.py

# Register emulator in frontend at http://localhost:8002
```

### Advantages over Go Emulator

- ✅ No Go runtime dependency
- ✅ Same language as serial communication library
- ✅ Easier to extend and modify
- ✅ Better integration with JS ecosystem
- ✅ Simpler build process
