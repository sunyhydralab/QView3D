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
  **Returns:** JSON response from `Issue.delete_issue(issueid)`

- `POST /editissue`  
  Edits an existing issue.  
  **Payload:** `{ "issueid": <int>, "issuenew": <str> }`  
  **Returns:** JSON response from `Issue.edit_issue(issueid, issuenew)`

---

### Jobs Controller (`server/controllers/jobs.py`)

- `GET /getjobs`  
  Returns a paginated list of jobs.

- `POST /addjobtoqueue`  
  Adds a job to a printer's in-memory queue.  
  **Payload:** `multipart/form-data` with job file and metadata.

- `POST /autoqueue`  
  Automatically assigns a job to the printer with the smallest queue.  
  **Payload:** `multipart/form-data` with job file and metadata.

- `POST /rerunjob`  
  Reruns a job on a specified printer.  
  **Payload:** `{ "printerpk": <int>, "jobpk": <int> }`

- `POST /jobdbinsert`  
  Inserts a job directly into the database.  
  **Payload:** `{ "jobdata": <dict> }`

- `POST /canceljob`  
  Cancels a queued or printing job.  
  **Payload:** `{ "jobpk": <int> }`

- `POST /cancelfromqueue`  
  Cancels multiple jobs from the queue.  
  **Payload:** `{ "jobarr": [<int>, ...] }`

- `POST /releasejob`  
  Releases a job from the queue and updates printer status.  
  **Payload:** `{ "jobpk": <int>, "key": <int>, "printerid": <int> }`

- `POST /bumpjob`  
  Changes the position of a job in the queue.  
  **Payload:** `{ "printerid": <int>, "jobid": <int>, "choice": <int> }`

- `POST /movejob`  
  Reorders jobs in a printer's queue.  
  **Payload:** `{ "printerid": <int>, "arr": [<int>, ...] }`

- `POST /updatejobstatus`  
  Updates the status of a job and removes it from the queue.  
  **Payload:** `{ "jobid": <int>, "status": <str> }`

- `POST /assigntoerror`  
  Assigns a job to error status and removes it from the queue.  
  **Payload:** `{ "jobid": <int>, "status": <str> }`

- `POST /deletejob`  
  Deletes a job by ID and removes it from the queue.  
  **Payload:** `{ "jobid": <int> }`

- `POST /setstatus`  
  Sets the status of a printer.  
  **Payload:** `{ "id": <int>, "status": <str> }`

- `GET /getfile`  
  Retrieves the G-code file for a job.  
  **Query:** `?jobid=<int>`

- `POST /nullifyjobs`  
  Nullifies all jobs for a printer.  
  **Payload:** `{ "printerid": <int> }`

- `GET /clearspace`  
  Clears space by removing old jobs/files.

- `GET /getfavoritejobs`  
  Returns a list of favorite jobs.

- `POST /favoritejob`  
  Sets a job as favorite.  
  **Payload:** `{ "jobid": <int>, "favorite": <bool> }`

- `POST /assignissue`  
  Assigns an issue to a job.  
  **Payload:** `{ "jobid": <int>, "issueid": <int> }`

- `POST /removeissue`  
  Removes an issue from a job.  
  **Payload:** `{ "jobid": <int> }`

- `POST /startprint`  
  Starts a print job (sets job and printer status).  
  **Payload:** `{ "printerid": <int>, "jobid": <int> }`

- `POST /savecomment`  
  Adds or updates a comment for a job.  
  **Payload:** `{ "jobid": <int>, "comments": <str> }`

- `GET`/`POST /downloadcsv`  
  Downloads jobs as a CSV file.  
  **Payload:** `{ "allJobs": <int>, "jobIds": [<int>, ...] }`

- `GET`/`POST /removeCSV`  
  Removes the temporary CSV file.

- `POST`/`GET /repairports`  
  Repairs printer port assignments.

- `POST`/`GET /refetchtimedata`  
  Refetches time data for a job.

---

### Ports Controller (`server/controllers/ports.py`)

- `GET /getports`  
  Returns a list of all connected ports.

- `GET /getfabricators`  
  Returns a list of all registered fabricators.

- `POST /register`  
  Registers a new fabricator with the system.  
  **Payload:** `{ "printer": { "device": { "serialPort": <str> }, "name": <str> } }`

- `POST /deletefabricator`  
  Deletes a fabricator from the system.  
  **Payload:** `{ "fabricator_id": <int> }`

- `POST /editname`  
  Edits the name of a registered fabricator.  
  **Payload:** `{ "fabricator_id": <int>, "name": <str> }`

- `POST /diagnose`  
  Diagnoses a fabricator based on its port.  
  **Payload:** `{ "device": <str> }`

- `POST /repair`  
  Repairs a fabricator based on its port.  
  **Payload:** `{ "device": <str> }`

- `POST /movehead`  
  Moves the head of a fabricator (deprecated if not needed).  
  **Payload:** `{ "port": <str> }`

- `POST /movefabricatorlist`  
  Changes the order of fabricators.  
  **Payload:** `{ "fabricator_ids": [<int>, ...] }`

- `POST /getfabricatorbyid`  
  Gets a fabricator by its ID.  
  **Payload:** `{ "fabricator_id": <int> }`

---

### Status Service Controller (`server/controllers/statusService.py`)

- `GET /getprinters`  
  Returns a list of all printers (fabricators).

- `GET /getprinterinfo`  
  Returns detailed information for all printers (including thread info).

- `POST /hardreset`  
  Performs a hard reset on a printer thread.  
  **Payload:** `{ "printerid": <int> }`

- `POST /queuerestore`  
  Restores the queue for a printer with a given status.  
  **Payload:** `{ "printerid": <int>, "status": <str> }`

- `POST /removethread`  
  Removes a printer thread.  
  **Payload:** `{ "printerid": <int> }`

- `POST /editNameInThread`  
  Edits the name of a fabricator in its thread.  
  **Payload:** `{ "fabricator_id": <int>, "newname": <str> }`

- `GET /serverVersion`  
  Returns the server version.

- `GET /status`  
  Returns the current status of the server/service.

- `GET /health`  
  Returns health check information.

- `GET /metrics`  
  Returns server metrics.

---

### Fabricators Controller (`server/controllers/fabricators.py`)

- `GET /getfabricators`  
  Returns a list of all fabricators (printers).

- `POST /createfabricator`  
  Creates a new fabricator/printer.  
  **Payload:** `{ ...fabricator fields... }`

- `POST /updatefabricator`  
  Updates an existing fabricator/printer.  
  **Payload:** `{ "fabricator_id": <int>, ...fields... }`

- `POST /deletefabricator`  
  Deletes a fabricator/printer by ID.  
  **Payload:** `{ "fabricator_id": <int> }`

- `GET /getfabricatorstatus`  
  Returns the status of a specific fabricator/printer.  
  **Query:** `?fabricator_id=<int>`

---

### Emulator Controller (`server/controllers/emulator.py`)

- `POST /startemulator`  
  Starts the printer emulator process and initiates a WebSocket connection.  
  **Payload:** `{ "model": <str>, "config": <dict> }`  
  **Returns:** `{ "message": "Emulator started successfully" }` or error message.

- `POST /registeremulator`  
  Registers the emulator with the backend and sends a registration event via WebSocket.  
  **Payload:** `{ ... }`  
  **Returns:** `{ "message": "Emulator registered successfully" }` or error message.

- `POST /disconnectemulator`  
  Disconnects the emulator and sends a disconnect event via WebSocket.  
  **Payload:** `{ ... }`  
  **Returns:** `{ "message": "Emulator disconnected successfully" }` or error message.

---

## WebSocket (Socket.IO) Events

WebSocket events are used for real-time updates between the server and frontend.  
These are typically emitted from backend logic using `current_app.socketio.emit(...)` or `socketio.emit(...)`.

### Emitted Events

#### From `Classes/Jobs.py`

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



