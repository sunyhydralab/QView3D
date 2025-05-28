# Project Structure

This document describes the organization of the QView3D server-side codebase.

## Top-Level Directories

- `server/`  
  Main backend application code. Contains all logic, API endpoints, and supporting modules for the backend.

- `docs/`  
  Documentation files.

## Server Directory Structure

The `server/` folder is organized as follows:

- `Classes/`  
  Contains core backend logic and data models.  
  - `Jobs.py`: Defines the Job class and job management logic, including job state, progress, and event emission.
  - `Issues.py`: Contains the Issue class and logic for tracking and managing issues related to jobs or fabricators.
  - `JobQueue.py`: Implements the job queue, managing job scheduling and execution order.
  - `JobStatus.py`: Defines job status constants and helpers for status transitions.
  - `Queue.py`: Provides additional queueing logic or abstractions for job/task management.
  - `Ports.py`: Contains logic for managing hardware ports, including opening, closing, and listing available ports.
  - `serialCommunication.py`: (If present) This file may contain logic for low-level serial communication with devices.  
    **Note:** Check the codebase to see if this file is currently imported or used by other modules. If it is not imported anywhere, it may be deprecated or unused.
  - `Fabricators/`: Contains logic and classes for managing fabricators (printers).
    - `Fabricator.py`: Defines the `Fabricator` class, which encapsulates the properties, state, and operations of a 3D printer or similar device.  
      This file typically includes methods for printer initialization, status updates, job assignment, and communication with the hardware.
    - `Device.py`: Defines the Device class, which represents a hardware device associated with a fabricator.
  - `FabricatorConnection.py`: Handles the connection logic between the backend and a fabricator device, including establishing, maintaining, and closing communication channels.
  - `FabricatorList.py`: Manages collections of Fabricator objects, providing methods to add, remove, and query available fabricators.

- `controllers/`  
  Flask route handlers for API endpoints.  
  - Each file (e.g., `jobs.py`, `issues.py`, `fabricators.py`, `ports.py`, `statusService.py`) defines routes for a specific resource or service.

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
│   ├── Fabricators/
│   │   ├── Device.py
│   │   └── Fabricator.py
│   ├── FabricatorConnection.py
│   ├── FabricatorList.py
│   ├── Issues.py
│   ├── JobQueue.py
│   ├── JobStatus.py
│   ├── Jobs.py
│   ├── Ports.py
│   ├── serialCommunication.py
│   └── Queue.py
├── app.py
├── config/
├── controllers/
│   ├── fabricators.py
│   ├── issues.py
│   ├── jobs.py
│   ├── ports.py
│   └── statusService.py
```


