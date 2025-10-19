# QView3D Architecture

## System Overview

QView3D uses a hybrid multi-backend architecture with intelligent routing and automatic fallback.

## Components

### Frontend (Port 8002)
- Vue 3 with Composition API
- TailwindCSS for styling
- WebSocket client for real-time updates
- GCode preview and 3D model visualization

### Middleware (Port 3500)
Express.js router that:
- Routes requests to appropriate backend based on endpoint patterns
- Provides automatic fallback if primary backend fails
- Handles WebSocket proxy connections

### Python Backend (Port 8000)
Flask server handling:
- Database operations (SQLite)
- Job management and queuing
- Issue tracking
- File uploads and storage

### JavaScript Backend (Port 3000)
Node.js server handling:
- Serial port communication
- Real-time printer control
- Virtual printer emulator
- Hardware detection

## Request Flow

```
Client Request → Middleware → Route Decision → Backend → Response
                     ↓
              Fallback Backend (if primary fails)
```

## Endpoint Routing

### JavaScript Priority
- `/api/fabricators/*` - Printer management
- `/api/emulator/*` - Virtual printer
- Serial communication endpoints

### Python Priority
- `/api/jobs/*` - Job management
- `/api/issues/*` - Issue tracking
- File upload endpoints

## WebSocket Architecture

Two WebSocket servers run in parallel:
- Python WS (8001): Job updates, queue changes
- JavaScript WS (3001): Real-time printer status, serial data

## Database

SQLite database managed by Python backend:
- Jobs and queue
- Issue tracking
- Printer configurations
- User settings