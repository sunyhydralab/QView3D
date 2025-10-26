# QView3D Middleware Architecture

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [How It Works](#how-it-works)
4. [Request Flow](#request-flow)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Backend Comparison](#backend-comparison)
8. [Development Guide](#development-guide)

---

## Overview

The QView3D middleware is a Node.js Express server that acts as a **reverse proxy** and **communication layer** between the Vue.js frontend and the backend services (Python Flask or Node.js). It provides:

- **Frontend Serving**: Delivers the Vue.js application from `client/dist`
- **API Proxying**: Routes API requests to the appropriate backend
- **WebSocket Proxying**: Forwards Socket.IO events bidirectionally
- **Backend Abstraction**: Shields the frontend from backend implementation details

### Key Benefits

1. **Single Entry Point**: Clients connect to one port (8002) regardless of backend
2. **Backend Switching**: Switch between Python/JavaScript backends without frontend changes
3. **Load Distribution**: Can distribute requests between multiple backend instances
4. **Development Flexibility**: Frontend and backend can be developed independently

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Browser                              │
│                   http://localhost:8002                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP/WebSocket
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  MIDDLEWARE SERVER (Port 8002)               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Express.js Server                                      │  │
│  │  - Static File Server (client/dist)                    │  │
│  │  - API Route Proxy                                     │  │
│  │  - SPA Fallback (Vue Router support)                   │  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Socket.IO Server                                       │  │
│  │  - Accepts client connections                          │  │
│  │  - Forwards events to backend                          │  │
│  │  - Broadcasts backend events to clients                │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTP/Socket.IO
                         ▼
        ┌────────────────┴────────────────┐
        │                                 │
        ▼                                 ▼
┌──────────────────┐            ┌──────────────────┐
│ Python Backend   │            │ JavaScript       │
│ (Port 8000)      │            │ Backend          │
│                  │            │ (Port 8005)      │
│ - Flask Server   │            │ - Express Server │
│ - Socket.IO      │            │ - WebSocket      │
│ - SQLAlchemy     │            │ - SQLite3        │
│ - PySerial       │            │ - SerialPort     │
│ - Full Features  │            │ - Core Features  │
└──────────────────┘            └──────────────────┘
        │                                 │
        └────────────────┬────────────────┘
                         │
                         ▼
               ┌──────────────────┐
               │  Serial Ports    │
               │  3D Printers     │
               │  Virtual Devices │
               └──────────────────┘
```

---

## How It Works

### 1. Frontend Serving

The middleware serves the compiled Vue.js application as static files:

```javascript
// Serve static files from Vue.js build
app.use(express.static(DIST_PATH)); // client/dist

// SPA fallback for Vue Router
app.use((req, res, next) => {
  if (req.method === 'GET') {
    res.sendFile(path.join(DIST_PATH, 'index.html'));
  }
});
```

**Flow:**
1. Browser requests `http://localhost:8002/`
2. Middleware serves `client/dist/index.html`
3. Browser loads Vue.js app and assets
4. Vue Router handles client-side navigation

### 2. API Proxying

API requests are proxied to the backend using `http-proxy-middleware`:

```javascript
const apiRoutes = [
  '/api',
  '/getfabricators',
  '/getjobs',
  '/getports',
  '/register',
  // ... 20+ more routes
];

apiRoutes.forEach(route => {
  app.use(route, createProxyMiddleware({
    target: 'http://localhost:8000',  // Currently hardcoded to Python
    changeOrigin: true,
    ws: route === '/socket.io'
  }));
});
```

**Flow:**
1. Frontend makes API call: `fetch('/getjobs')`
2. Middleware intercepts the request
3. Proxies to backend: `http://localhost:8000/getjobs`
4. Backend processes and returns response
5. Middleware forwards response to frontend

### 3. Socket.IO Proxying

Real-time events are forwarded bidirectionally:

```javascript
// Middleware acts as Socket.IO CLIENT to backend
backendSocket = ioClient('http://localhost:8000');

// Middleware acts as Socket.IO SERVER to frontend
io.on('connection', (socket) => {
  // Forward client events to backend
  socket.onAny((event, ...args) => {
    backendSocket.emit(event, ...args);
  });

  // Forward backend events to all clients
  backendSocket.onAny((event, ...args) => {
    io.emit(event, ...args);
  });
});
```

**Flow:**
1. Frontend connects to middleware Socket.IO
2. Middleware maintains connection to backend
3. Events flow: Frontend → Middleware → Backend
4. Broadcasts: Backend → Middleware → All Frontends

### 4. Route Mapping System

The middleware includes intelligent routing configuration (currently not fully utilized):

**File:** `middleware/src/config/routes.js`

```javascript
export const routeMap = {
  // JavaScript backend specialized routes
  '/api/serial': 'javascript',
  '/api/gcode': 'javascript',

  // Both backends support these ('either' = use active backend)
  '/getjobs': 'either',
  '/getfabricators': 'either',
  '/register': 'either',

  // Python-only advanced features
  '/diagnose': 'python',
  '/repair': 'python',
  '/bumpjob': 'python',
  '/movejob': 'python'
};
```

**Routing Modes:**
- `'python'` - Always route to Python backend
- `'javascript'` - Always route to JavaScript backend
- `'either'` - Route to currently selected backend

---

## Request Flow

### Example: Job History Request

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ GET /getjobs?page=1&pageSize=10
       ▼
┌─────────────────────┐
│   Middleware:8002   │
│  - Matches /getjobs │
│  - Proxies request  │
└──────┬──────────────┘
       │ GET http://localhost:8000/getjobs?page=1&pageSize=10
       ▼
┌─────────────────────┐
│  Python Backend     │
│  - Queries SQLite   │
│  - Returns JSON     │
└──────┬──────────────┘
       │ Response: { jobs: [...], total: 42 }
       ▼
┌─────────────────────┐
│   Middleware        │
│  - Forwards response│
└──────┬──────────────┘
       │ Response: { jobs: [...], total: 42 }
       ▼
┌─────────────────────┐
│   Browser           │
│  - Updates UI       │
└─────────────────────┘
```

### Example: Printer Status Update (WebSocket)

```
┌─────────────────────┐
│  Python Backend     │
│  Printer prints line│
└──────┬──────────────┘
       │ emit('printer_progress', { id: 1, progress: 45.2 })
       ▼
┌─────────────────────┐
│  Middleware         │
│  Socket.IO Client   │
└──────┬──────────────┘
       │ broadcast to all clients
       ▼
┌─────────────────────┐
│  All Browsers       │
│  Update dashboards  │
└─────────────────────┘
```

---

## Configuration

### Backend Configuration

**File:** `middleware/src/config/backends.js`

Loads configuration from `server-python/config/config.json`:

```json
{
  "middleware": {
    "mode": "python",
    "port": 8002
  },
  "backends": {
    "python": {
      "url": "http://localhost:8000",
      "port": 8000,
      "ws_port": 8000,
      "emulator_port": 8004
    },
    "javascript": {
      "url": "http://localhost:8005",
      "port": 8005,
      "ws_port": 8005,
      "emulator_port": 8007
    }
  }
}
```

**Configuration Options:**
- `middleware.mode`: Default backend ('python' or 'javascript')
- `middleware.port`: Middleware server port (default: 8002)
- `backends.*.url`: Backend base URL
- `backends.*.emulator_port`: Port for virtual printer emulator

### Startup Configuration

The `run.py` script updates `config.json` before starting services:

```python
def update_config_json():
    config['middleware'] = {
        "port": MIDDLEWARE_PORT,
        "mode": BACKEND_MODE  # User selected: 'python' or 'javascript'
    }
```

---

## API Reference

### Middleware-Specific Endpoints

#### `GET /api/middleware/health`
Health check for middleware status.

**Query Parameters:**
- `debug=true` - Include backend status information

**Response:**
```json
{
  "status": "healthy",
  "server_backend": "python",
  "server_url": "http://localhost:8000",
  "server_status": {
    "status": "healthy",
    "uptime": 12345.67
  }
}
```

#### `POST /api/middleware/select-backend` (Planned)
Switch between Python and JavaScript backends.

**Request Body:**
```json
{
  "backend": "javascript"
}
```

**Response:**
```json
{
  "success": true,
  "active_backend": "javascript",
  "backend_url": "http://localhost:8005"
}
```

### Proxied API Routes

All routes in the `apiRoutes` array are proxied to the backend:

**Core Routes:**
- `/api/*` - All API endpoints
- `/getfabricators` - List registered printers
- `/getjobs` - Job history with pagination
- `/getports` - Available serial ports
- `/register` - Register new printer
- `/addjobtoqueue` - Upload and queue print job
- `/startprint` - Start printing a job
- `/canceljob` - Cancel print job
- `/startemulator` - Create virtual printer
- `/getissues` - List issues
- `/health` - Backend health check

**Total:** 30+ proxied routes

---

## Backend Comparison

### Feature Matrix

| Feature | Python Backend | JavaScript Backend | Notes |
|---------|---------------|-------------------|-------|
| **Framework** | Flask + Socket.IO | Express + WebSocket | Python more mature |
| **Database** | SQLAlchemy ORM | SQLite3 raw | Python more abstracted |
| **Serial Communication** | PySerial | @serialport/stream | Both functional |
| **Job Management** | ✅ Full | ✅ Core | Python has advanced features |
| **Printer Registration** | ✅ | ✅ | Feature parity |
| **Queue Management** | ✅ Advanced | ✅ Basic | Python has reordering |
| **G-code Simulation** | ✅ | ❌ | Python only |
| **Virtual Printers** | ✅ Advanced | ✅ Basic | Python simulates temperature |
| **Issue Tracking** | ✅ | ✅ | Feature parity |
| **CSV Export** | ✅ | ❌ | Python only |
| **Diagnostics** | ✅ | ❌ | Python only |
| **Port Repair** | ✅ | ❌ | Python only |

### Endpoint Coverage

**Python Backend:** ~45 endpoints (100% coverage)
**JavaScript Backend:** ~30 endpoints (~70% coverage)

### Missing from JavaScript Backend

**Advanced Job Management:**
- `/bumpjob` - Reorder job in queue
- `/movejob` - Move job between printers
- `/releasejob` - Release job back to pool
- `/rerunjob` - Restart failed job

**Hardware Operations:**
- `/diagnose` - Hardware diagnostics
- `/repair` - Port repair utilities
- `/movehead` - Manual head positioning
- `/repairports` - Port recovery

**Analytics & Reporting:**
- `/downloadcsv` - Export job history
- `/removeCSV` - Clean up exports
- `/refetchtimedata` - Recalculate job times
- `/clearspace` - Storage cleanup
- `/nullifyjobs` - Bulk job operations

**Database Operations:**
- `/jobdbinsert` - Direct database insert

---

## Development Guide

### Running the Middleware

```bash
# Start in development mode
cd middleware
npm run dev

# Start in production mode
npm start
```

### Adding a New Proxied Route

1. **Add to apiRoutes array** in `middleware/src/index.js`:

```javascript
const apiRoutes = [
  // ... existing routes
  '/mynewroute'  // Add here
];
```

2. **Implement in backend:**
   - Python: `server-python/routes/`
   - JavaScript: `server-javascript/src/routes/`

3. **Add to route map** (optional) in `middleware/src/config/routes.js`:

```javascript
export const routeMap = {
  '/mynewroute': 'either'  // or 'python' / 'javascript'
};
```

### Implementing Intelligent Routing

To use the route mapping system, modify the proxy configuration:

```javascript
app.use('/', createProxyMiddleware({
  router: (req) => {
    const backend = getBackendForRoute(req.path);
    return backend.url;
  }
}));
```

### Testing

**Current Status:** ❌ No middleware tests implemented

**Planned Tests:**
```bash
# Unit tests for route mapping
npm test

# Integration tests
npm run test:integration
```

**Test Framework:** Node.js test runner (built-in)

### Debugging

Enable debug logging:

```javascript
// In middleware/src/index.js
const DEBUG = true;

if (DEBUG) {
  console.log(`[Proxy] ${req.method} ${req.path} → ${target}`);
}
```

Access health endpoint with debug info:
```bash
curl http://localhost:8002/api/middleware/health?debug=true
```

---

## Current Limitations & Roadmap

### Known Issues

1. **Hardcoded Backend Target** ⚠️
   - Currently hardcoded to `localhost:8000` (Python)
   - Route mapping system exists but not fully utilized
   - **Impact:** Can't dynamically switch backends

2. **No Backend Health Monitoring** ⚠️
   - Middleware doesn't check if backend is alive
   - No automatic failover or retry logic
   - **Impact:** Errors when backend is down

3. **No Load Balancing** ⚠️
   - Can't distribute load across multiple backend instances
   - **Impact:** Single point of failure

4. **Missing Tests** ⚠️
   - No test suite for middleware
   - **Impact:** Regressions hard to catch

### Improvement Roadmap

**Phase 1: Dynamic Routing (Priority: HIGH)**
- [ ] Enable route-based backend selection
- [ ] Implement backend switching API
- [ ] Add configuration validation

**Phase 2: Reliability (Priority: HIGH)**
- [ ] Add backend health checks
- [ ] Implement automatic reconnection
- [ ] Add request retry logic
- [ ] Graceful error handling

**Phase 3: Testing (Priority: MEDIUM)**
- [ ] Unit tests for routing logic
- [ ] Integration tests for proxy behavior
- [ ] E2E tests for full stack

**Phase 4: Performance (Priority: MEDIUM)**
- [ ] Request caching for read-only endpoints
- [ ] Connection pooling
- [ ] Compression optimization

**Phase 5: Scalability (Priority: LOW)**
- [ ] Load balancing across multiple backends
- [ ] Backend instance registration
- [ ] Health-based routing

**Phase 6: Observability (Priority: LOW)**
- [ ] Request logging and metrics
- [ ] Performance monitoring
- [ ] Analytics dashboard

---

## Troubleshooting

### Middleware Won't Start

**Symptom:** `EADDRINUSE` error
**Cause:** Port 8002 already in use
**Solution:**
```bash
# Kill process on port 8002
# Linux/Mac:
lsof -ti:8002 | xargs kill -9
# Windows:
netstat -ano | findstr :8002
taskkill /PID <pid> /F
```

### Frontend Not Loading

**Symptom:** 404 error on `/`
**Cause:** Frontend not built
**Solution:**
```bash
cd client
npm run build-only
```

### API Requests Fail

**Symptom:** 500 errors, "Backend connection failed"
**Cause:** Backend not running
**Solution:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Start backend if needed
cd server-python
python app.py
```

### WebSocket Not Connecting

**Symptom:** Socket.IO connection errors in browser console
**Cause:** Middleware can't connect to backend Socket.IO
**Solution:**
1. Check backend Socket.IO is running on port 8000
2. Check firewall/network settings
3. Verify CORS configuration

---

## Architecture Decisions

### Why a Middleware Layer?

**Alternative 1: Direct Backend Connection**
- ❌ Frontend needs to know which backend to connect to
- ❌ Can't switch backends without frontend changes
- ❌ No centralized point for monitoring/logging

**Alternative 2: Backend-Served Frontend**
- ✅ Simpler architecture
- ❌ Backend must serve static files
- ❌ Mixing concerns (API + static serving)
- ❌ Harder to scale independently

**Chosen: Middleware Proxy**
- ✅ Clean separation of concerns
- ✅ Backend-agnostic frontend
- ✅ Enables backend switching
- ✅ Centralized monitoring point
- ✅ Can add caching, rate limiting, etc.

### Why Socket.IO Proxying?

Direct WebSocket proxying is complex. Socket.IO provides:
- ✅ Automatic reconnection
- ✅ Fallback to polling if WebSocket fails
- ✅ Event-based API (easier to proxy)
- ✅ Room/namespace support for future scaling

---

## Contributing

When modifying the middleware:

1. **Test both backends** - Ensure Python and JavaScript backends work
2. **Update documentation** - Keep this file current
3. **Add tests** - Write tests for new functionality
4. **Check performance** - Profile proxy overhead
5. **Update route maps** - Document new routes in `routes.js`

---

## Version History

**v1.0.0** (Current)
- Serves Vue.js frontend from `client/dist`
- Proxies 30+ API routes to backend
- Socket.IO bidirectional proxying
- Hardcoded to Python backend (port 8000)
- Route mapping configuration (not fully utilized)
- Health check endpoint

**Planned for v1.1.0:**
- Dynamic backend selection
- Backend health monitoring
- Test suite implementation
- Intelligent route-based proxying

---

## References

- **http-proxy-middleware:** https://github.com/chimurai/http-proxy-middleware
- **Socket.IO:** https://socket.io/docs/v4/
- **Express.js:** https://expressjs.com/
- **Vue.js:** https://vuejs.org/

---

*Last Updated: 2025-10-26*
*Maintained by: QView3D Development Team*
