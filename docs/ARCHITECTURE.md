# QView3D Architecture

## System Overview

QView3D uses a multi-backend architecture with middleware-based routing.

## Components

### Frontend (Port 8002)
- Vue 3 with Composition API
- TailwindCSS for styling
- WebSocket client for real-time updates
- GCode preview and 3D model visualization

### Middleware (Port 3500)
Express.js proxy that:
- Routes all requests to the configured backend (Python or JavaScript)
- Acts as a transparent proxy layer
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

### Request Routing Diagram

```mermaid
flowchart LR
    Client[Client Request] --> Middleware
    Middleware --> Decision{Route Decision}
    Decision -->|Frontend Assets| Vite[Vite Server<br/>5173]
    Decision -->|API Request| Backend[Selected Backend<br/>Python or JavaScript]
    Backend --> Response[JSON Response]
    Vite --> Response
    Response --> Client

    style Client fill:#e1f5ff
    style Middleware fill:#90ee90
    style Backend fill:#4169e1
    style Response fill:#90ee90
```

## Backend Capabilities

### Python Backend
- Job management and queuing
- Issue tracking
- File uploads and storage
- Database operations (SQLite)

### JavaScript Backend
- Serial port communication
- Real-time printer control
- Virtual printer emulator
- Hardware detection

## WebSocket Architecture

Two WebSocket servers run in parallel:
- Python WS (8001): Job updates, queue changes
- JavaScript WS (3001): Real-time printer status, serial data

### WebSocket Communication Flow

```mermaid
sequenceDiagram
    participant F as Frontend Client
    participant M as Middleware<br/>WebSocket
    participant PW as Python WS<br/>(8001)
    participant JW as JavaScript WS<br/>(3001)

    F->>M: Connect WebSocket
    M->>PW: Connect to Python WS
    M->>JW: Connect to JavaScript WS

    Note over F,JW: Job Update Flow
    PW->>M: emit('job_update')
    M->>F: Broadcast to all clients

    Note over F,JW: Printer Status Flow
    JW->>M: emit('printer_status')
    M->>F: Broadcast to all clients

    Note over F,JW: Client Command Flow
    F->>M: emit('start_print')
    M->>PW: Forward to Python
    PW-->>M: Acknowledgment
    M-->>F: Confirm
```

## Database

SQLite database managed by Python backend:
- Jobs and queue
- Issue tracking
- Printer configurations
- User settings

### Database Relationships

```mermaid
erDiagram
    FABRICATORS ||--o{ JOBS : "prints"
    JOBS ||--o| ISSUES : "has"
    FABRICATORS {
        int id PK
        string name
        string devicePort
        string hwid
        string status
        int position
    }
    JOBS {
        int id PK
        string name
        int fabricator_id FK
        string status
        string file_name
        blob file_blob
        int issue_id FK
        datetime time_start
        datetime time_end
    }
    ISSUES {
        int id PK
        string title
        string description
        string severity
        datetime created_at
    }
```