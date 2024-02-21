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
import time 
import gzip
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary(16777215), nullable=False)
    name = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)
    # foreign key relationship to match jobs to the printer printed on 
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'), nullable = False)
    printer = db.relationship('Printer', backref='Job')
    file_name_original = db.Column(db.String(50), nullable = False)
    file_name_pk = None

    
    def __init__(self, file, name, printer_id, status, file_name_original): 
        self.file = file 
        self.name = name 
        self.printer_id = printer_id 
        self.status = status 
        self.file_name_original = file_name_original # original file name without PK identifier 
        file_name_pk = None

    def __repr__(self):
        return f"Job(id={self.id}, name={self.name}, printer_id={self.printer_id}, status={self.status})"
    
    def getPrinterId(self): 
        return self.printer_id
        
    @classmethod
    def get_job_history(cls, page, pageSize, printerIds=None, oldestFirst=False):
        try:
            query = cls.query
            if printerIds:
                query = query.filter(cls.printer_id.in_(printerIds))

            if oldestFirst:
                query = query.order_by(cls.date.asc())
            else: 
                query = query.order_by(cls.date.desc())  # Change this line

            pagination = query.paginate(page=page, per_page=pageSize, error_out=False)
            jobs = pagination.items

            jobs_data = [{
                "id": job.id,
                "name": job.name, 
                "status": job.status, 
                "date": f"{job.date.strftime('%a, %d %b %Y %H:%M:%S')} {get_localzone().tzname(job.date)}",  
                "printer": job.printer.name, 
                "file_name_original": job.file_name_original
            } for job in jobs]

            return jobs_data, pagination.total
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to retrieve jobs. Database error"}), 500

        
    @classmethod
    def jobHistoryInsert(cls, name, printer_id, status, file, file_name_original): 
        try:
            if isinstance(file, bytes):
                file_data = file
            else:
                file_data = file.read()
                
            try:
                gzip.decompress(file_data)
                compressed_data = file_data  # If it decompresses successfully, it's already compressed
            except OSError:
                compressed_data = gzip.compress(file_data)  
                            
            job = cls(
                file = compressed_data, 
                name=name,
                printer_id=printer_id,
                status=status,
                file_name_original = file_name_original
            )

            db.session.add(job)
            db.session.commit()
        
            return {"success": True, "message": "Job added to collection.", "id": job.id}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to add job. Database error"}),
                500,
            ) 
    
    @classmethod
    def update_job_status(cls, job_id, new_status):
        try:
            # Retrieve the job from the database based on its primary key
            job = cls.query.get(job_id)
            if job:
                # Update the status attribute of the job
                job.status = new_status
                # Commit the changes to the database
                db.session.commit()
                return {"success": True, "message": f"Job {job_id} status updated successfully."}
            else:
                return {"success": False, "message": f"Job {job_id} not found."}, 404
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to update job status. Database error"}),
                500,
            )
                    
    @classmethod 
    def findJob(cls, job_id):
        try:
            job = cls.query.filter_by(id=job_id).first()
            return job
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to retrieve job. Database error"}), 500  
        
    @classmethod
    def removeFileFromPath(cls, file_path):
        # file_path = self.generatePath()  # Get the file path
        if os.path.exists(file_path):    # Check if the file exists
            os.remove(file_path)         # Remove the file 
            
    @classmethod 
    def setDBstatus(cls, jobid, status):
        cls.update_job_status(jobid, status)

    @classmethod 
    def getPathForDelete(cls, file_name):
        return os.path.join('../uploads', file_name)
           
    def saveToFolder(self):
        file_data = self.getFile()
        decompressed_data = gzip.decompress(file_data) 
        with open(self.generatePath(), 'wb') as f:
            f.write(decompressed_data)
    
    def generatePath(self):
        return os.path.join('../uploads', self.getFileNamePk())
    
    #getters 
    def getName(self):
        return self.name
    
    def getFilePath(self):
        return self.path 
    
    def getFile(self): 
        return self.file
    
    def getStatus(self): 
        return self.status 
    
    def getFileNamePk(self):
        return self.file_name_pk
    
    def getFileNameOriginal(self):
        return self.file_name_original
    
    def getPrinterId(self): 
        return self.printer_id
    
    def getJobId(self):
        return self.id
    
    #setters 
    def setStatus(self, status): 
        self.status = status
            
    def setPath(self, path): 
        self.path = path 

    def setFileName(self, filename):
        self.file_name_pk = filename
        
    def setFile(self, file):
        self.file = file