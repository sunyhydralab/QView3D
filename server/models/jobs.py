import base64
import os
from models.db import db 
from datetime import datetime, timezone
from models.printers import Printer
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask import jsonify 
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from tzlocal import get_localzone
from io import BytesIO
from werkzeug.datastructures import FileStorage
# model for job history table 
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary(16777215), nullable=False)
    name = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)
    # foreign key relationship to match jobs to the printer printed on 
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'), nullable = False)
    printer = db.relationship('Printer', backref='Job')
    path = None
    
    job_id = 1
    id_counter = 1 
    
    def __init__(self, file, name, printer_id, status='inqueue', file_name=None, path=None): 
        # if file is not provided, load it in from the path
        if file==None and file_name!=None: 
            self.setFile(file_name)
        else: 
            self.file = file 
            
        self.name = name 
        self.printer_id = printer_id 
        self.status = status # set default status to be in-queue
        self.date = datetime.now(get_localzone())
        self.file_name = file_name
        self.path = path 
        
        self.job_id = Job.id_counter  # Assign a unique ID
        Job.id_counter += 1  # Increment the counter for the next object
        
        self.saveToFolder()
    
    def getPrinterId(self): 
        return self.printer_id
        
    @classmethod
    def get_job_history(cls):
        try:
            jobs = cls.query.all()
            
            jobs_data = [{
                "file_name": job.file_name, 
                "name": job.name, 
                "status": job.status, 
                "date": f"{job.date.strftime('%a, %d %b %Y %H:%M:%S')} {get_localzone().tzname(job.date)}",  
                "printer": job.printer.name
            } for job in jobs]
            print(jobs_data)
            
            return jobs_data
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to retrieve jobs. Database error"}), 500
        
    @classmethod
    def jobHistoryInsert(cls, name, printer_id, status, file_name, file_path): 
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                file_storage = FileStorage(stream=BytesIO(file_data), filename=file_name)

                
            # file_storage = FileStorage(stream=BytesIO(file_data), filename=file_name)  
            
            job = cls(
                file = file_data, 
                name=name,
                printer_id=printer_id,
                status=status,
                file_name=file_name
            )

            db.session.add(job)
            db.session.commit()
            return {"success": True, "message": "Job added to collection."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to add job. Database error"}),
                500,
            )
            
    def setFile(self, file_name): 
        path = self.generatePath(file_name)
        if self.fileExistsInPath(path):
            with open(path, 'rb') as file:
                file_data = file.read()
            
            file_storage = FileStorage(stream=BytesIO(file_data), filename=file_name)  
            
            # path = self.generatePath(file_name)
            self.file = file_storage
        else: 
            self.file = self.loadFileFromDB(file_name)
           
    def saveToFolder(self):
        file_name = self.getFileName()
        file_path = self.generatePath(file_name)
        file = self.getFile()
        if isinstance(file, bytes):
            file = FileStorage(stream=BytesIO(file), filename=file_name)
        file.save(file_path)
        self.setPath(file_path)
        return file_path
    
    def loadFileFromDB(self, file_name):
        job = Job.query.filter_by(file_name=file_name).first()  # Query the database for a job with the same file_name
        if job is not None:
            print(f"job.file type: {type(job.file)}")
            print(f"job.file value: {job.file}")
            stream = BytesIO(job.file)
            print(f"stream type: {type(stream)}")
            print(f"stream value: {stream.getvalue()}")
            return FileStorage(stream=stream, filename=job.file_name) # Create a FileStorage object from the job's file data
        else:
            return "File not found in database."
    
    @classmethod
    def generatePath(self, filename):
        folder_path = os.path.join("..", "uploads")
        file_path = os.path.join(folder_path, filename)
        return file_path 
    
    @classmethod
    def deleteFile(cls, path):
        if cls.fileExistsInPath(path):
            os.remove(path)
        
    @classmethod 
    def fileExistsInPath(self, path): 
        if os.path.exists(path):
            return True
    
    def getName(self):
        return self.name
    
    def getFilePath(self):
        return self.path 
    
    def getFile(self): 
        return self.file
    
    def openFile(self, file):
        # open the file in binary mode
        file = open(file, 'rb')
        return file        
    
    def closeFile(self, file):
        # close the file
        file.close()
    
    def getStatus(self): 
        return self.status 
    
    def getFileName(self):
        return self.file_name
    
    def getPrinterId(self): 
        return self.printer_id
    
    def getJobId(self):
        return self.job_id
    
    def setStatus(self, status): 
        self.status = status
        
    def setPath(self, path): 
        self.path = path 
        