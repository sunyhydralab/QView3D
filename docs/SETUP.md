# Setup Guide

## Prerequisites

- Python 3.12+
- Node.js 18+
- npm
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/sunyhydralab/QView3D.git
cd QView3D
```

2. Install dependencies:
```bash
python run.py
# Select 'I' for install
```

## Running the Application

### Quick Start
```bash
python run.py
# Select 'D' for debug mode (Python backend by default)
```

### Backend Selection
```bash
python run.py
# Select 'B' to choose backend mode
```

Options:
- **Python Backend**: Traditional Flask server (mode 1)
- **JavaScript Backend**: Node.js with serial support (mode 2)

### Startup Sequence Diagram

```mermaid
flowchart TB
    Start([Run python run.py]) --> Menu{Select Option}

    Menu -->|I - Install| Install[Install Dependencies]
    Menu -->|D - Debug| Debug[Debug Mode]
    Menu -->|B - Backend| Backend[Backend Selection]

    Install --> PyDeps[Install Python<br/>Dependencies]
    PyDeps --> NodeDeps[Install Node.js<br/>Dependencies]
    NodeDeps --> Done([Setup Complete])

    Debug --> ConfigDefault[Write config.json<br/>mode: python]
    ConfigDefault --> StartVite[Start Vite Dev Server<br/>Port 5173]
    StartVite --> StartMiddleware[Start Middleware<br/>Port 8002]
    StartMiddleware --> ReadConfig[Middleware reads config<br/>Sets BACKEND_TARGET_URL]
    ReadConfig --> StartPython[Start Python Backend<br/>Port 8000]
    StartPython --> Ready([Application Ready])

    Backend --> Choice{Choose Backend}
    Choice -->|Python| PythonMode[Write config.json<br/>mode: python]
    Choice -->|JavaScript| JSMode[Write config.json<br/>mode: javascript]

    PythonMode --> StartVite
    JSMode --> StartVite

    Ready --> Access[Access via<br/>http://localhost:8002]

    style Start fill:#e1f5ff
    style ConfigDefault fill:#ffeb3b
    style PythonMode fill:#ffeb3b
    style JSMode fill:#ffeb3b
    style ReadConfig fill:#ffeb3b
    style Ready fill:#90ee90
    style Access fill:#ffd700
```

## Manual Setup

### Frontend
```bash
cd client
npm install
npm run dev
```

### Python Backend
```bash
cd server-python
python -m venv .python-venv
# Windows: .python-venv\Scripts\activate
# Linux/Mac: source .python-venv/bin/activate
pip install -r dependencies.txt
flask run
```

### JavaScript Backend
```bash
cd server-javascript
npm install
npm start
```

### Middleware
```bash
cd middleware
npm install
node src/index.js
```

## Configuration

### Ports
- Frontend: 8002
- Python API: 8000
- JavaScript API: 3000
- Middleware: 3500

### Port Configuration Diagram

```mermaid
flowchart LR
    User[User Browser] -->|Port 8002| MW[Middleware]

    subgraph Services
        MW -->|Frontend<br/>5173| Vite[Vite Dev]
        MW -->|API<br/>Static Target| Target[Selected Backend]
        Target -.->|mode: python<br/>8000| Py[Python API]
        Target -.->|mode: javascript<br/>8005| JS[JS API]
    end

    Py --> DB[(SQLite<br/>QView.db)]
    JS --> DB

    style User fill:#e1f5ff
    style MW fill:#90ee90
    style Target fill:#ffeb3b
    style DB fill:#ff6347
```

### Database
- Location: `server-python/QView.db`
- Reset: Delete file for fresh start

## Testing

### Virtual Printer
Access the emulator at http://localhost:8002/emulator

### Running Tests
```bash
# Frontend
cd client && npm run test:unit

# JavaScript Backend
cd server-javascript && npm test
```

## Troubleshooting

### Port Conflicts
Check if ports 3000, 3500, 8000-8002 are available

### Serial Port Access
- Windows: Run as administrator
- Linux: Add user to dialout group

### Python Version
Ensure Python 3.12+ is installed

### Database Issues
Delete `server-python/QView.db` to reset