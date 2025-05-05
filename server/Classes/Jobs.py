from operator import or_
import os
import re
from models.db import db
from models.issues import Issue  # assuming the Issue model is defined in the issue.py file in the models directory
from datetime import timezone, timedelta
from flask import jsonify
from globals import current_app
from traceback import format_exc
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import gzip
import csv
from flask import send_file

class Job(db.Model):
    __tablename__ = 'Jobs'

    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary(16777215), nullable=True)
    name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(
        timezone.utc).astimezone(), nullable=False)
    # foreign key relationship to match jobs to the printer printed on
    fabricator_id = db.Column(db.Integer, db.ForeignKey('Fabricators.dbID'), nullable=True)

    fabricator = db.relationship('Fabricator', backref='Job')

    fabricator_name = db.Column(db.String(50), nullable=True)

    # TeamDynamics ID
    td_id = db.Column(db.Integer, nullable=True)

    # FK to issue
    error_id = db.Column(db.Integer, db.ForeignKey('Issues.id'), nullable=True)
    error = db.relationship('Issue', backref='Issue')

    # comments
    comments = db.Column(db.String(500), nullable=True)

    file_name_original = db.Column(db.String(50), nullable=False)
    favorite = db.Column(db.Boolean, nullable=False)
    file_name_pk = None
    max_layer_height = 0.0
    current_layer_height = 0.0
    filament = ''
    released = False
    filePause = False
    progress = 0.0
    sent_lines = 0
    time_started = 0
    extruded = 0
    # total, eta, timestart, pause time
    job_time = [0, datetime.min, datetime.min, datetime.min]
    job_logger = None

    def __init__(self, file, name, fabricator_id, status, file_name_original, favorite, td_id, fabricator_name):
        self.path = None
        self.file = file
        self.name = name
        self.fabricator_id = fabricator_id
        self.status = status
        self.file_name_original = file_name_original  # original file name without PK identifier
        self.td_id = td_id
        self.file_name_pk = None
        self.file_path = None
        self.favorite = favorite
        self.released = 0
        self.filePause = 0
        self.progress = 0.0
        self.sent_lines = 0
        self.time_started = 0
        self.extruded = 0
        self.job_time = [0, datetime.min, datetime.min, datetime.min]
        self.error_id = 0
        self.fabricator_name = fabricator_name
        self.max_layer_height = 0.0
        self.current_layer_height = 0.0
        self.filament = ''

    def __repr__(self):
        return f"Job(id={self.id}, name={self.name}, printer_id={self.fabricator_id}, status={self.status})"

    def __to_JSON__(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "date": self.date.strftime('%a, %d %b %Y %H:%M:%S'),
            "printerid": self.fabricator_id,
            "errorid": self.error_id,
            "file_name_original": self.file_name_original,
            "progress": self.progress,
            "sent_lines": self.sent_lines,
            "favorite": self.favorite,
            "released": self.released,
            "file_pause": self.filePause,
            "comments": self.comments,
            "extruded": self.extruded,
            "td_id": self.td_id,
            "time_started": self.time_started,
            "printer_name": self.fabricator_name,
            "max_layer_height": self.max_layer_height,
            "current_layer_height": self.current_layer_height,
            "filament": self.filament,
        }
    def getPrinterId(self):
        return self.fabricator_id

    @classmethod
    def get_job_history(
            cls,
            page,
            pageSize,
            printerIds=None,
            oldestFirst=False,
            searchJob="",
            searchCriteria="",
            searchTicketId=None,
            favoriteOnly=False,
            issueIds=None,
            startDate=None,
            endDate=None,
            fromError=None,
            countOnly=None
    ):
        try:
            query = cls.query
            if (fromError == 1):
                query = cls.query.filter_by(status="error")

            if printerIds:
                query = query.filter(cls.fabricator_id.in_(printerIds))

            if issueIds:
                query = query.filter(cls.error_id.in_(issueIds))

            if searchJob:
                searchJob = f"%{searchJob}%"
                query = query.filter(
                    or_(
                        cls.name.ilike(searchJob),
                        cls.file_name_original.ilike(searchJob),
                    )
                )

            if "searchByJobName" in searchCriteria:
                searchByJobName = f"%{searchJob}%"
                query = query.filter(cls.name.ilike(searchByJobName))
            elif "searchByFileName" in searchCriteria:
                searchByFileName = f"%{searchJob}%"
                query = query.filter(cls.file_name_original.ilike(searchByFileName))

            if searchTicketId:
                searchTicketId = int(searchTicketId)
                query = query.filter(cls.td_id == searchTicketId)

            if favoriteOnly:
                query = query.filter(cls.favorite == True)

            if oldestFirst:
                query = query.order_by(cls.date.asc())
            else:
                query = query.order_by(cls.date.desc())  # Change this line

            if startDate != '' or endDate != '':
                if (endDate == ''):
                    cls.date.between(
                        datetime.fromisoformat(startDate),
                        datetime.fromisoformat(startDate),
                    )

                query = query.filter(
                    cls.date.between(
                        datetime.fromisoformat(startDate),
                        datetime.fromisoformat(endDate),
                    )
                )

            pagination = query.paginate(page=page, per_page=pageSize, error_out=False)
            jobs = pagination.items

            jobs_data = [job.__to_JSON__()
                for job in jobs
            ]
            if countOnly == 0:
                return jobs_data, pagination.total
            else:
                return pagination.total

        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def jobHistoryInsert(cls, name: str, fabricator_id: int, status: str, file, file_name_original: str, favorite: bool = False, td_id: int = 0):
        """
        Inserts a new job into the database. It first checks if the file is already compressed. If it is, it uses the existing compressed data.
        :param str name: The name of the job.
        :param int fabricator_id: The ID of the fabricator.
        :param str status: The status of the job.
        :param file: The file associated with the job. It can be a bytes object or a file-like object.
        :param str file_name_original: The original name of the file.
        :param bool favorite: Whether the job is marked as favorite. Default is False.
        :param int td_id: The Team Dynamics ID associated with the job. Default is 0.
        """
        try:
            if isinstance(file, bytes):
                file_data = file
            else:
                file.seek(0)
                file_data = file.read()

            try:
                gzip.decompress(file_data)
                # If it decompresses successfully, it's already compressed
                compressed_data = file_data
            except OSError:
                compressed_data = gzip.compress(file_data)
            from Classes.Fabricators.Fabricator import Fabricator
            fabricator = Fabricator.query.get(fabricator_id)

            job = cls(
                file=compressed_data,
                name=name,
                fabricator_id=fabricator_id,
                status=status,
                file_name_original = file_name_original,
                favorite = favorite,
                td_id = td_id,
                fabricator_name = fabricator.name
            )

            db.session.add(job)
            db.session.commit()

            return {"success": True, "message": "Job added to collection.", "id": job.id}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def update_job_status(cls, job_id: int, new_status: str):
        try:
            # Retrieve the job from the database based on its primary key
            job = cls.query.get(job_id)
            if job:
                # Update the status attribute of the job
                job.status = new_status
                # Commit the changes to the database
                if current_app:
                    db.session.commit()
                    current_app.socketio.emit('job_status_update', {
                        'job_id': job_id, 'status': new_status})

                return {"success": True, "message": f"Job {job_id} status updated successfully."}
            else:
                return {"success": False, "message": f"Job {job_id} not found."}, 404
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def delete_job(cls, job_id: int):
        try:
            job = cls.query.get(job_id)
            if job:
                db.session.delete(job)
                db.session.commit()
                return {"success": True, "message": f"Job with ID {job_id} deleted from the database."}
            else:
                return {"error": f"Job with ID {job_id} not found in the database."}
        except Exception as e:
            # When an error occurs or an exception is raised during a database operation (such as adding,
            # updating, or deleting records), it may leave the database in an inconsistent state. To handle such
            # situations, a rollback is performed to revert any changes made within the current session to maintain the integrity of the database.
            if current_app:
                db.session.rollback()
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Unexpected error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def findJob(cls, job_id: int):
        try:
            job = cls.query.filter_by(id=job_id).first()
            return job
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def removeFileFromPath(cls, file_path: str):
        # file_path = self.generatePath()  # Get the file path
        if os.path.exists(file_path):  # Check if the file exists
            os.remove(file_path)  # Remove the file

    @classmethod
    def setDBstatus(cls, jobid: int, status: str):
        cls.update_job_status(jobid, status)

    @classmethod
    def getPathForDelete(cls, file_name: str):
        return os.path.join('../uploads', file_name)

    @classmethod
    def nullifyPrinterId(cls, printer_id: int):
        try:
            jobs = cls.query.filter_by(fabricator_id=printer_id).all()
            for job in jobs:
                job.fabricator_id = 0
            db.session.commit()
            return {"success": True, "message": "Printer ID nullified successfully."}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def clearSpace(cls):
        try:
            six_months_ago = datetime.now() - timedelta(days=182)  # 6 months ago
            old_jobs = Job.query.filter(Job.date < six_months_ago).all()

            # thirty_seconds_ago = datetime.now() - timedelta(seconds=30)  # 30 seconds ago
            # old_jobs = Job.query.filter(Job.date < thirty_seconds_ago).all()

            for job in old_jobs:
                if (job.favorite == 0):
                    job.file = None  # Set file to None
                    if "Removed after 6 months" not in job.file_name_original:
                        job.file_name_original = f"{job.file_name_original}: Removed after 6 months"
            db.session.commit()  # Commit the changes
            return {"success": True, "message": "Space cleared successfully."}
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def getFavoriteJobs(cls):
        try:
            jobs = cls.query.filter_by(favorite=True).all()
            return [job.__to_JSON__() for job in jobs]
        except SQLAlchemyError as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def setIssue(cls, job_id: int, issue_id: int):
        job = cls.query.get(job_id)

        if job is None:
            return None

        # Set the job's error_id to the given issue_id
        job.error_id = issue_id

        # Commit the changes to the database
        try:
            db.session.commit()
            return {"success": True, "message": "Issue assigned successfully."}
        except Exception as e:
            if current_app:
                db.session.rollback()
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def unsetIssue(cls, job_id: int):
        job = cls.query.get(job_id)

        if job is None:
            return None

        # Set the job's error_id to None
        job.error_id = None

        # Commit the changes to the database
        try:
            db.session.commit()
            return {"success": True, "message": "Issue removed successfully."}
        except Exception as e:
            if current_app:
                db.session.rollback()
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def setComment(cls, job_id: int, comments: str):
        job = cls.query.get(job_id)

        if job is None:
            return None

        # Set the job's comments to the given comments
        job.comments = comments

        # Commit the changes to the database
        try:
            db.session.commit()
            return {"success": True, "message": "Comments added successfully."}
        except Exception as e:
            if current_app:
                db.session.rollback()
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Database error: {e}")
            return jsonify({"error": format_exc()}), 500

    @classmethod
    def downloadCSV(cls, alljobs, jobids=None):
        try:
            if (jobids != None):
                # Join Job and Issue on error_id and filter by jobids
                jobs = db.session.query(cls, Issue).outerjoin(Issue, cls.error_id == Issue.id).filter(
                    cls.id.in_(jobids)).all()
            else:
                # Join Job and Issue on error_id
                jobs = db.session.query(cls, Issue).outerjoin(Issue, cls.error_id == Issue.id).all()

            # Specify the columns you want to include
            column_names = ['td_id', 'printer', 'name', 'file_name_original', 'status', 'date', 'issue', 'comments']

            date_string = datetime.now().strftime("%m%d%Y")

            csv_file_name = f'../tempcsv/jobs_{date_string}.csv'

            # Write to CSV

            with open(csv_file_name, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(column_names)  # write headers
                for job, issue in jobs:
                    row = [getattr(job, 'td_id', ''), getattr(job, 'printer_name', ''), getattr(job, 'name', ''),
                           getattr(job, 'file_name_original', ''), getattr(job, 'status', ''), getattr(job, 'date', ''),
                           getattr(issue, 'issue', '') if issue else '', getattr(job, 'comments', '')]
                    writer.writerow(row)  # write data rows

            csv_file_path = f'./{csv_file_name}'

            return send_file(csv_file_path, as_attachment=True)


        except Exception as e:
            if current_app:
                current_app.handle_errors_and_logging(e)
            else:
                print(f"Error downloading CSV: {e}")
            return jsonify({"error": format_exc()}), 500

    def saveToFolder(self):
        file_data = self.file
        decompressed_data = gzip.decompress(file_data)
        self.file_path = self.generatePath()
        with open(self.file_path, 'wb') as f:
            f.write(decompressed_data)

    def generatePath(self):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", self.file_name_original)

    # getters
    def getName(self):
        return self.name

    def getLogger(self):
        return self.job_logger

    def getFilePath(self):
        return self.path

    def getFile(self):
        return self.file

    def getStatus(self) -> str:
        return self.status

    def getFileNamePk(self) -> str:
        return self.file_name_pk

    def getFileNameOriginal(self) -> str:
        return self.file_name_original

    def getFileFavorite(self) -> bool:
        return self.favorite

    def setFileFavorite(self, favorite: bool) -> dict:
        self.favorite = favorite
        db.session.commit()
        return {"success": True, "message": "Favorite status updated successfully."}

    def getJobId(self) -> int:
        return self.id

    def getFilePause(self):
        return self.filePause

    def setFilePause(self, pause: bool):
        self.filePause = pause
        if current_app:
            current_app.socketio.emit('file_pause_update', {
                'job_id': self.id, 'file_pause': self.filePause})

    def getExtruded(self) -> int:
        return self.extruded

    def setExtruded(self, extruded: bool):
        self.extruded = extruded
        if current_app:
            current_app.socketio.emit('extruded_update', {
                'job_id': self.id, 'extruded': self.extruded})

        # setters

    def setStatus(self, status: str):
        self.status = status
        # self.setDBstatus(self.id, status)

    # added a setProgress method to update the progress of a job
    # which sends it to the frontend using socketio
    def setProgress(self, progress: float):
        if self.status == 'printing':
            self.progress = progress
            # Emit a 'progress_update' event with the new progress
            if current_app:
                current_app.socketio.emit(
                    'progress_update', {'job_id': self.id, 'progress': self.progress})

    # added a getProgress method to get the progress of a job
    def getProgress(self) -> float:
        return self.progress

    def setSentLines(self, sent_lines: int):
        self.sent_lines = sent_lines
        # current_app.socketio.emit('gcode_viewer', {'job_id': self.id, 'gcode_num': self.sent_lines})

    def getSentLines(self) -> int:
        return self.sent_lines

    @staticmethod
    def getTimeFromFile(comment_lines: list[str]) -> int:
        # job_line can look two ways:
        # 1. ;TIME:seconds
        # 2. ; estimated printing time (normal mode) = minutes seconds
        # if first line contains "FLAVOR", then the second line contains the time estimate in the format of ";TIME:seconds"
        if "FLAVOR" in comment_lines[0]:
            time_line = comment_lines[1]
            time_seconds = int(time_line.split(":")[1])
        else:
            # search for the line that contains "printing time", then the time estimate is in the format of "; estimated printing time (normal mode) = minutes seconds"
            time_line = next((line for line in comment_lines if "time" in line), None)
            if not time_line:
                return 0
            time_values = re.findall(r'\d+', time_line)

            # Initialize all time units to 0
            time_days = time_hours = time_minutes = time_seconds = 0

            # Assign values from right to left (seconds, minutes, hours, days)
            time_values = time_values[::-1]
            if len(time_values) > 0:
                time_seconds = int(time_values[0])
            if len(time_values) > 1:
                time_minutes = int(time_values[1])
            if len(time_values) > 2:
                time_hours = int(time_values[2])
            if len(time_values) > 3:
                time_days = int(time_values[3])

            # Calculate total time in seconds
            time_seconds = time_days * 24 * 60 * 60 + time_hours * 60 * 60 + time_minutes * 60 + time_seconds
        # date = datetime.fromtimestamp(time_seconds)
        return time_seconds

    def getTimeStarted(self):
        return self.time_started

    def calculateEta(self):
        now = datetime.now()
        eta = timedelta(seconds=self.job_time[0]) + now
        return eta

    def updateEta(self):
        now = datetime.now()
        pause_time = self.getJobTime()[3]

        duration = now - pause_time

        new_eta = self.getJobTime()[1] + timedelta(seconds=1)
        return new_eta

    def colorEta(self):
        print("before ETA: ", self.getJobTime()[1])

        now = datetime.now()
        pause_time = self.getJobTime()[3]
        duration = now - pause_time
        eta = self.getJobTime()[1] + duration
        return eta

    def calculateTotalTime(self) -> float:
        total_time = self.getJobTime()[0]

        # Add one second to total_time
        total_time += 1
        return total_time

    def calculateColorChangeTotal(self) -> float:
        print("before Total Time: ", self.getJobTime()[0])

        now = datetime.now()
        pause_time = self.getJobTime()[3]
        duration = now - pause_time
        duration_in_seconds = duration.total_seconds()
        total_time = self.getJobTime()[0] + duration_in_seconds
        return total_time

    def getJobTime(self) -> list:
        return self.job_time

    def getReleased(self):
        return self.released

    def getTdId(self) -> int:
        return self.td_id

    def setMaxLayerHeight(self, max_layer_height):
        self.max_layer_height = max_layer_height
        if current_app:
            current_app.socketio.emit('max_layer_height', {'job_id': self.id, 'max_layer_height': self.max_layer_height})

    def setCurrentLayerHeight(self, current_layer_height):
        self.current_layer_height = current_layer_height
        if current_app:
            current_app.socketio.emit('current_layer_height', {'job_id': self.id, 'current_layer_height': self.current_layer_height})

    def setFilament(self, filament):
        self.filament = filament

    def setPath(self, path):
        self.path = path

    def setFileName(self, filename):
        self.file_name_pk = filename

    def setFile(self, file):
        self.file = file

    def setReleased(self, released):
        self.released = released
        if current_app:
            current_app.socketio.emit('release_job', {'job_id': self.id, 'released': released})

    def setTimeStarted(self, time_started):
        self.time_started = time_started
        if current_app:
            current_app.socketio.emit('set_time_started', {'job_id': self.id, 'started': time_started})

    def setTime(self, timeData, index):
        # timeData = datetime(y, m, d, h, min, s)
        # print("TimeData: ", timeData, " Index: ", index)
        self.job_time[index] = timeData
        if current_app:
            if index == 0:
                current_app.socketio.emit('set_time', {'job_id': self.id, 'new_time': timeData, 'index': index})
            else:
                current_app.socketio.emit('set_time', {'job_id': self.id, 'new_time': timeData.isoformat(), 'index': index})