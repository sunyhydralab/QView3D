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

# model for job history table 
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary, nullable=False)
    name = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(50), nullable=False)
    file_name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).astimezone(), nullable=False)
    
    # foreign key relationship to match jobs to the printer printed on 
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'), nullable = False)
    
    printer = db.relationship('Printer', backref='Job')
    
    # file_name = None 
    
    def __init__(self, file, name, printer_id, status='inqueue', file_name=None): 
        self.file = file 
        self.name = name 
        self.printer_id = printer_id 
        self.status = status # set default status to be in-queue
        self.date = datetime.now(get_localzone())
        self.file_name = file_name
        # file_name =  base64.b64encode(self.file).decode('utf-8') if self.file else None
    
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
        
    # insert into job history 
    @classmethod
    def jobHistoryInsert(cls, file, name, printer_id, status, file_name): 
        try:
            job = cls(
                file=file,
                name=name,
                printer_id=printer_id,
                status=status,
                file_name=file_name
            )
            db.session.add(job)
            db.session.commit()
            print("Job added to collection.")
            return {"success": True, "message": "Job added to collection."}
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return (
                jsonify({"error": "Failed to add job. Database error"}),
                500,
            )
        
    def getName(self):
        return self.name
    
    def getFile(self):
        # Open the file in binary mode and return the file object
        file_path = os.path.join("..", "uploads", self.file.filename)
        return file_path
    
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
    
    def setStatus(self, status): 
        self.status = status
        
    def saveToFolder(file):
    # if folder doesn't exist, create it
    # save the file to a folder
        folder_path = os.path.join("..", "uploads")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        file_path = os.path.join(folder_path, file.filename)
        file.save(file_path)
        return file_path
    
    def deleteFile(self):
        # get job file path
        file_path = os.path.join("..", "uploads", self.file.filename)
        # delete the file
        os.remove(file_path)