# Project Structure

This document describes the organization of the QView3D server-side codebase.

## Top-Level Directories

- `server/`  
  Main backend application code. Contains all logic, API endpoints, and supporting modules for the backend.

## Server Directory Structure

The `server/` folder is organized as follows:

- `Classes/`  
  Contains core backend logic and data models.  
  - `EventEmitter.py`: Provides event-driven programming support for emitting and handling custom events.
  - `FabricatorConnection.py`: Handles the connection logic between the backend and a fabricator device, including establishing, maintaining, and closing communication channels.
  - `FabricatorList.py`: Manages collections of Fabricator objects, providing methods to add, remove, and query available fabricators.
  - `Jobs.py`: Defines the Job class and job management logic, including job state, progress, and event emission.
  - `Ports.py`: Contains logic for managing hardware ports, including opening, closing, and listing available ports.
  - `Queue.py`: Provides additional queueing logic or abstractions for job/task management.
  - `serialCommunication.py`: Test file for serial communication, can be run without full server setup.
  - `Vector3.py`: Defines a 3D vector class.
  - `Fabricators/`: Contains logic and classes for managing fabricators (printers).
    - `Fabricator.py`: Defines the `Fabricator` class, which encapsulates the properties, state, and operations of a 3D printer or similar device.
      This file typically includes methods for printer initialization, status updates, job assignment, and communication with the hardware.
    - `Device.py`: Defines the Device class, which represents a hardware device associated with a fabricator.

- `controllers/`  
  Flask route handlers for API endpoints.  
  - `emulator.py`: Endpoints for starting, registering, and disconnecting printer emulators.
  - `issues.py`: Endpoints for issue tracking and management.
  - `jobs.py`: Endpoints for job management (create, update, delete, etc.).
  - `ports.py`: Endpoints for managing hardware ports.
  - `statusService.py`: Endpoints for server status, health, and metrics.

- `utils/`  
  Utility functions and helpers used throughout the backend.

- `config/`  
  Configuration files and environment settings.

- `app.py`  
  Main Flask application entry point. Initializes the app, registers controllers, and sets up extensions (e.g., Socket.IO).

## File Tree

```text
server/
├── Classes/
│   ├── EventEmitter.py
│   ├── FabricatorConnection.py
│   ├── FabricatorList.py
│   ├── Jobs.py
│   ├── Ports.py
│   ├── Queue.py
│   ├── serialCommunication.py
│   ├── Vector3.py
│   └── Fabricators/
│       ├── Device.py
│       └── Fabricator.py
├── app.py
├── config/
├── controllers/
│   ├── emulator.py
│   ├── issues.py
│   ├── jobs.py
│   ├── ports.py
│   └── statusService.py
```


