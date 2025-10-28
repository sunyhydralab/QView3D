# QView3D Middleware

Static proxy server for QView3D 3D printer management system. Routes all frontend and API requests to a single backend configured at startup.

## System Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser[Browser<br/>localhost:8002]
    end

    subgraph Middleware["Middleware Layer - Port 8002"]
        MW[Express.js Proxy Server]
        MWSIO[Socket.IO Server]
    end

    subgraph Frontend["Frontend Dev"]
        Vite[Vite Dev Server<br/>Port 5173<br/>Vue.js + HMR]
    end

    subgraph Backends["Backend Services"]
        BackendChoice{Backend Mode<br/>Set at Startup}
        Python[Python Flask<br/>Port 8000<br/>Full Features]
        JS[JavaScript Express<br/>Port 8005<br/>Core Features]
    end

    subgraph Data["Data Layer"]
        DB[(SQLite Database<br/>qview.db)]
    end

    subgraph Hardware["Hardware Layer"]
        Serial[Serial Ports]
        Printers[3D Printers]
        Emulator[Virtual Printers<br/>Port 8004/8007]
    end

    Browser <-->|HTTP/WebSocket| MW
    MW -->|Frontend Assets| Vite
    MW -->|API Routes| BackendChoice

    BackendChoice -.->|mode: python| Python
    BackendChoice -.->|mode: javascript| JS

    Browser <-->|Socket.IO| MWSIO
    MWSIO <-->|Socket.IO| Python
    MWSIO <-->|WebSocket| JS

    Python --> DB
    JS --> DB

    Python --> Serial
    JS --> Serial

    Serial --> Printers
    Serial --> Emulator

    style Browser fill:#e1f5ff
    style MW fill:#90ee90
    style MWSIO fill:#90ee90
    style Vite fill:#ffd700
    style BackendChoice fill:#ffeb3b
    style Python fill:#4169e1
    style JS fill:#32cd32
    style DB fill:#ff6347
    style Serial fill:#ffa500
    style Printers fill:#ff69b4
    style Emulator fill:#9370db
```

## Request Flow

### Frontend Asset Loading
```mermaid
sequenceDiagram
    participant B as Browser
    participant M as Middleware<br/>(8002)
    participant V as Vite<br/>(5173)

    Note over M: Startup: Proxy configured

    B->>M: GET /
    M->>V: Proxy request
    V->>V: Compile Vue.js
    V-->>B: HTML + JS + HMR WebSocket

    Note over B,V: Live updates during development
    B->>M: WebSocket (HMR)
    M->>V: Forward HMR events
```

### API Request Flow
```mermaid
sequenceDiagram
    participant B as Browser
    participant M as Middleware<br/>(8002)
    participant BE as Backend<br/>(8000 or 8005)
    participant DB as SQLite

    Note over M: Startup: Read config.mode<br/>Set BACKEND_TARGET_URL

    B->>M: GET /api/getfabricators
    M->>BE: Proxy to backend
    BE->>DB: Query fabricators
    DB-->>BE: Return data
    BE-->>M: JSON response
    M-->>B: Forward response
```

### Real-time Updates
```mermaid
sequenceDiagram
    participant B as Browser
    participant M as Middleware<br/>Socket.IO Server
    participant BE as Backend<br/>Socket.IO/WebSocket

    B->>M: Connect Socket.IO
    M->>BE: Connect to backend

    Note over B,BE: Bidirectional event proxying

    B->>M: Emit event (e.g., start_print)
    M->>BE: Forward event

    BE->>M: Emit update (e.g., printer_status)
    M->>B: Broadcast to all clients
```

## Configuration

**File:** `middleware/src/config/backends.js`

```javascript
export default {
  middleware: {
    mode: "python",  // "python" or "javascript"
    port: 8002       // Middleware port
  },
  backends: {
    python: {
      url: "http://localhost:8000"
    },
    javascript: {
      url: "http://localhost:8005"
    }
  }
};
```

## Port Configuration

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **Middleware** | 8002 | HTTP/WS | Main entry point (access app here) |
| **Vite Dev** | 5173 | HTTP/WS | Frontend development with HMR |
| **Python Backend** | 8000 | HTTP/WS | Flask + PySerial + full features |
| **JavaScript Backend** | 8005 | HTTP/WS | Express + SerialPort + core features |
| **Emulator (Python)** | 8004 | HTTP | Virtual printer (Python) |
| **Emulator (JS)** | 8007 | HTTP | Virtual printer (JavaScript) |

## Technology Stack

### Middleware
- **Express.js 5.x** - Web server
- **http-proxy-middleware 3.x** - Proxy routing
- **Socket.IO 4.x** - Real-time bidirectional events
- **cors 2.x** - Cross-origin support

### Python Backend
- **Flask 3.x** - Web framework
- **Flask-SocketIO 5.x** - WebSocket support
- **SQLAlchemy 2.x** - Database ORM
- **PySerial 3.5+** - Serial communication
- **Eventlet 0.37+** - Async WSGI server

### JavaScript Backend
- **Express.js 5.x** - Web framework
- **sqlite3 5.x** - Database
- **@serialport/stream 13.x** - Serial communication
- **ws 8.x** - WebSocket

### Frontend
- **Vue.js 3** - UI framework
- **Vite 4.x** - Build tool with HMR
- **Bootstrap** - Styling

### Database
- **SQLite3** - Embedded database
- **Tables:** fabricators, jobs, queue, issues

## Running the Middleware

### Via run.py (Recommended)
```bash
python3 run.py
# Select 'D' for debug mode
# Middleware starts automatically
```

### Manually
```bash
cd middleware
npm install
npm start
```

### Debug Mode
```bash
DEBUG=true npm start
```
With `DEBUG=true`, middleware logs all proxied requests.

## API Routes Proxied

The middleware proxies these routes to the backend:

**Core API:**
- `/api/*` - All namespaced API endpoints

**Fabricator Management:**
- `/getfabricators`, `/registerfabricator`, `/deletefabricator`
- `/pauseprinter`, `/resumeprinter`, `/cancelprinter`
- `/getprinterinfo`, `/setstatus`

**Job Management:**
- `/getjobs`, `/addjob`, `/canceljob`, `/startprint`, `/releasejob`
- `/getjobhistory`, `/uploadfiles`, `/getfiles`, `/deletefile`

**Queue Management:**
- `/getqueue`, `/reorderqueue`, `/clearqueue`, `/autoqueue`
- `/addjobtoqueue`, `/cancelfromqueue`

**Emulator Management:**
- `/startemulator`, `/registeremulator`, `/disconnectemulator`
- `/getports`, `/register`

**Issue Tracking:**
- `/getissues`, `/createissue`, `/updateissue`, `/deleteissue`, `/resolveissue`

**System:**
- `/health`, `/serverVersion`
- `/socket.io` - WebSocket connection

**All other routes** → Proxied to Vite dev server (frontend assets)

## Health Check

```bash
curl http://localhost:8002/api/middleware/health
```

**Response:**
```json
{
  "status": "healthy",
  "backends": {
    "python": {
      "status": "healthy",
      "responseTime": 45
    },
    "javascript": {
      "status": "offline",
      "responseTime": null
    }
  }
}
```

**Debug mode:**
```bash
curl http://localhost:8002/api/middleware/health?debug=true
```

Returns full middleware config, uptime, and backend details.

## Key Features

### 1. Static Routing
- Backend selected ONCE at startup from config
- No per-request routing decisions
- Simple pass-through proxy for performance
- Restart required to change backend

### 2. Frontend Hot Module Replacement
- Vite WebSocket proxied automatically
- Instant updates (~200ms) during development
- No build step required

### 3. Socket.IO Bidirectional Proxying
- Middleware acts as Socket.IO server to clients
- Middleware acts as Socket.IO client to backend
- All events forwarded automatically
- Broadcasts to all connected clients

### 4. Health Monitoring
- Checks backend status every 10 seconds
- Warns if routing to unhealthy backend
- Exposes status via `/api/middleware/health`

### 5. Error Handling
- 500 for backend processing errors
- 502 for backend unavailable
- Detailed error messages in debug mode

## Development Notes

### Emulator Access
Virtual printers (emulators) route through middleware on port 8002, just like physical printers.

### Path Rewriting
API routes with `/api/` prefix are rewritten:
- Request: `GET /api/createissue`
- Proxied to: `GET /createissue` (prefix stripped)

Backend routes don't use `/api/` prefix internally.

### Backend Health Warnings
If backend is unhealthy, middleware logs warnings but still attempts to proxy:
```
[Proxy] WARNING: Routing to unhealthy backend (python): /getfabricators
```

### WebSocket Support
- Frontend HMR: Handled by Vite WebSocket
- Real-time updates: Handled by Socket.IO
- Both protocols proxied transparently

## Troubleshooting

**Middleware won't start:**
```bash
cd middleware
npm install
# Check if port 8002 is available
lsof -i :8002
```

**Vite connection failed:**
```bash
# Make sure Vite dev server is running
cd frontend
npm run dev
# Should start on port 5173
```

**Backend connection failed:**
```bash
# Check backend is running
python3 run.py  # Select 'D' for debug mode
# Python backend should start on port 8000
```

**Socket.IO not connecting:**
- Check browser console for connection errors
- Verify backend Socket.IO is running
- Check middleware logs for backend connection status

## Architecture Decisions

### Why Static Routing?
- **Simplicity:** No complex routing logic
- **Performance:** Direct proxy with no overhead
- **Reliability:** Fewer moving parts
- **Development:** Easy to reason about request flow

### Why Single Backend per Run?
- Backends are not interchangeable (Python has more features)
- No need for load balancing (single-user system)
- Simpler configuration and debugging
- Clear system state

### Why Middleware at All?
- **Single entry point:** Clients connect to one port
- **Development flexibility:** Frontend and backend developed independently
- **Frontend HMR:** Vite dev server proxied seamlessly
- **Backend abstraction:** Frontend doesn't need to know backend implementation

## File Structure

```
middleware/
├── src/
│   ├── config/
│   │   └── backends.js       # Backend configuration
│   ├── healthCheck.js         # Backend health monitoring
│   └── index.js               # Main middleware server
├── test/                      # Test files
├── package.json               # Dependencies
└── README.md                  # This file
```
