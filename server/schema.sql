CREATE TABLE Logs (
    id INTEGER PRIMARY KEY,
    content VARCHAR(4096),
    job_id INTEGER,
    type INTEGER,
    FOREIGN KEY (job_id) REFERENCES Jobs(id)
);

CREATE TABLE Fabricators (
    id INTEGER PRIMARY KEY,
    hardware_id VARCHAR(128),
    custom_name VARCHAR(256),
    date_registered DATETIME,
    model_name VARCHAR(256)
);

CREATE TABLE Jobs (
    id INTEGER PRIMARY KEY,
    gcode_file_id INTEGER,
    status INTEGER,
    date_created DATETIME,
    date_completed DATETIME,
    name VARCHAR(128),
    ticket_id INTEGER,
    fabricator_id INTEGER,
    fabricator_queue_index INTEGER,
    is_favorited BOOLEAN,
    FOREIGN KEY (gcode_file_id) REFERENCES GcodeFiles(id),
    FOREIGN KEY (fabricator_id) REFERENCES Fabricators(id)
);

CREATE TABLE Gcode (
    id INTEGER PRIMARY KEY,
    gcode_file BLOB,
    gcode_file_name VARCHAR(256)
);
