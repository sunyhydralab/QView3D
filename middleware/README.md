# QView3D Middleware

API gateway middleware for routing between Python and JavaScript backends.

## Overview

The middleware acts as a transparent proxy that routes requests to the selected backend based on the configured mode:

- **Python Mode**: All requests go to Python backend (default)
- **JavaScript Mode**: All requests go to JavaScript backend

## Architecture

```
Client <-> Middleware (Port 3500) <-> Python Backend (Port 8000)
                                  <-> JavaScript Backend (Port 3000)
```

### Architecture Diagram

```mermaid
flowchart LR
    Client[Client Browser] <-->|HTTP/WS<br/>Port 3500| MW[Middleware<br/>Express.js]

    subgraph Backends[Backend Services]
        Python[Python Backend<br/>Port 8000<br/>Flask + Socket.IO]
        JS[JavaScript Backend<br/>Port 3000<br/>Express + WebSocket]
    end

    MW <-->|Route Based| Python
    MW <-.->|Route Based| JS

    Python --> DB[(SQLite<br/>qview.db)]
    JS --> DB

    subgraph Hardware[Hardware Layer]
        Serial[Serial Ports]
        Printers[3D Printers]
        Emulators[Virtual Printers]
    end

    Python --> Serial
    JS --> Serial
    Serial --> Printers
    Serial --> Emulators

    style Client fill:#e1f5ff
    style MW fill:#90ee90
    style Python fill:#4169e1
    style JS fill:#32cd32
    style DB fill:#ff6347
```

## Features

- Automatic backend health monitoring
- Request proxying to the selected backend
- Response normalization between backends
- WebSocket proxy support
- Request/response logging

## Configuration

Configuration is loaded from `server/config/config.json`:

```json
{
  "middleware": {
    "mode": "python",
    "port": 3500,
    "ws_port": 3501
  },
  "backends": {
    "python": {
      "url": "http://localhost:8000",
      "ws_port": 8001
    },
    "javascript": {
      "url": "http://localhost:3000",
      "ws_port": 3001
    }
  }
}
```

## Route Mapping

All requests are routed to the configured backend (Python or JavaScript) based on the mode setting in `config.json`. The middleware acts as a simple proxy to the selected backend.

### Route Flow

```mermaid
flowchart TD
    Request[Incoming Request] --> Middleware{Middleware<br/>Mode Check}

    Middleware -->|Python Mode| PyBackend[Python Backend<br/>Port 8000]
    Middleware -->|JavaScript Mode| JSBackend[JavaScript Backend<br/>Port 3000]

    JSBackend --> Response[Return Response]
    PyBackend --> Response

    style Request fill:#e1f5ff
    style Middleware fill:#90ee90
    style JSBackend fill:#32cd32
    style PyBackend fill:#4169e1
    style Response fill:#90ee90
```

## Usage

### Starting the Middleware

The middleware is automatically started when you select backend mode via `run.py`:

```bash
python run.py
# Select [B] for Backend Selection
# Choose mode 1 for Python or mode 2 for JavaScript
```

### Manual Start

```bash
cd middleware
npm install
npm start
```

### Development Mode

```bash
npm run dev
```

## API Endpoints

### Health Check

```
GET /health
```

Returns middleware and backend status.

## Environment Variables

- `LOG_LEVEL`: Set logging level (ERROR, WARN, INFO, DEBUG)
- `NODE_ENV`: Set to 'production' to hide error details

## Backend Capabilities

### Python Backend
- Full database integration (SQLite)
- Complete job management system
- Fabricator registration and control
- Issue tracking
- Advanced diagnostics and repair tools
- Discord bot integration
- Emulator support

### JavaScript Backend
- SQLite database support
- Job management (create, queue, cancel, status)
- Fabricator registration and management
- Issue tracking
- Serial port communication
- WebSocket real-time updates
- Optimized for performance

## Backend Health Monitoring

The middleware performs health checks every 30 seconds on the configured backend:

- Marks backend as healthy/unhealthy
- Exposes status via `/health` endpoint
- Reports backend availability

## Response Normalization

The middleware normalizes responses between backends to ensure consistent API:

- Printer state mapping (numeric to string)
- Job data structure alignment
- Port list format standardization

## Error Handling

- Returns proper HTTP status codes
- Includes error details in development mode
- Logs all errors with context
- Returns 502 errors when backend is unavailable
