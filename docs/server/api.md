# API Reference

This section documents how the frontend communicates with the backend, including both HTTP REST API endpoints and WebSocket (Socket.IO) events.

---

## HTTP Endpoints

HTTP endpoints are defined in `server/controllers/` using Flask route decorators.

### Issues Controller (`server/controllers/issues.py`)

- `GET /getissues`  
  Returns a list of all issues.

- `POST /getissuebyjob`  
  Returns the issue associated with a specific job.  
  **Payload:** `{ "jobId": <int> }`

- `POST /createissue`  
  Creates a new issue (optionally linked to a job).  
  **Payload:** `{ "issue": <str>, "job": <int or null> }`

- `POST /deleteissue`  
  Deletes an issue by ID.  
  **Payload:** `{ "issueid": <int> }`

- `POST /editissue`  
  Edits an existing issue.  
  **Payload:** `{ "issueid": <int>, "issuenew": <str> }`

---

### Jobs Controller (`server/controllers/jobs.py`)

- `GET /getjobs`  
  Returns a paginated list of jobs.

- `POST /createjob`  
  Creates a new job.  
  **Payload:** `{ ...job fields... }`

- `POST /updatejobstatus`  
  Updates the status of a job.  
  **Payload:** `{ "job_id": <int>, "status": <str> }`

- `POST /deletejob`  
  Deletes a job by ID.  
  **Payload:** `{ "job_id": <int> }`

- `POST /setfavorite`  
  Sets a job as favorite.  
  **Payload:** `{ "job_id": <int>, "favorite": <bool> }`

- `POST /setcomment`  
  Adds or updates a comment for a job.  
  **Payload:** `{ "job_id": <int>, "comments": <str> }`

- `GET /downloadcsv`  
  Downloads jobs as a CSV file.

---

### Ports Controller (`server/controllers/ports.py`)

- `GET /getports`  
  Returns a list of available ports.

- `POST /openport`  
  Opens a specified port.  
  **Payload:** `{ "port": <str> }`

- `POST /closeport`  
  Closes a specified port.  
  **Payload:** `{ "port": <str> }`

---

### Status Service Controller (`server/controllers/statusService.py`)

- `GET /status`  
  Returns the current status of the server/service.

- `GET /health`  
  Returns health check information.

- `GET /metrics`  
  Returns server metrics.

---

## WebSocket (Socket.IO) Events

WebSocket events are used for real-time updates between the server and frontend.  
These are typically emitted from backend logic (e.g., in `Classes/Jobs.py`) using `current_app.socketio.emit(...)`.

### Emitted Events (from `Classes/Jobs.py`)

- `job_status_update`  
  Payload: `{ "job_id": <int>, "status": <str> }`

- `progress_update`  
  Payload: `{ "job_id": <int>, "progress": <float> }`

- `file_pause_update`  
  Payload: `{ "job_id": <int>, "file_pause": <bool> }`

- `extruded_update`  
  Payload: `{ "job_id": <int>, "extruded": <int> }`

- `max_layer_height`  
  Payload: `{ "job_id": <int>, "max_layer_height": <float> }`

- `current_layer_height`  
  Payload: `{ "job_id": <int>, "current_layer_height": <float> }`

- `release_job`  
  Payload: `{ "job_id": <int>, "released": <bool> }`

- `set_time_started`  
  Payload: `{ "job_id": <int>, "started": <int> }`

- `set_time`  
  Payload: `{ "job_id": <int>, "new_time": <varies>, "index": <int> }`

// ...Add any additional events from other backend files as needed...

---

**Note:**  
- The frontend listens for these events using the Socket.IO client.
- For more details, see the relevant backend class files (e.g., `Classes/Jobs.py`) and frontend event handlers.
