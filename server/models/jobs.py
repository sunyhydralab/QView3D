from models.db import db 
from datetime import datetime
from models.printers import Printer
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask import jsonify 
from sqlalchemy.exc import SQLAlchemyError

# model for job history table 
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary, nullable=False)
    name = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    
    # foregin key relationship to match jobs to the printer printed on 
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'), nullable = False)
    printer = db.relationship('Printer', backref='Job')
    
    def __init__(self, file, name, printer_id, status='inqueue'): 
        self.file = file 
        self.name = name 
        self.printer_id = printer_id 
        self.status = status # set default status to be in-queue
    
    def getPrinterId(self): 
        return self.printer_id
        
    @classmethod
    def get_job_history(cls):
        try:
            jobs = cls.query.all()
            
            jobs_data = [{
                "file": jobs.file, 
                "name": jobs.name, 
                "status": jobs.status, 
                "date": jobs.date, 
                "printer": {
                    "name": Printer.name
                }
            } for job in jobs]
            
            return jsonify({"jobs": jobs_data})
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return jsonify({"error": "Failed to retrieve jobs. Database error"}), 500
        
    # insert into job history 
    @classmethod
    def jobHistoryInsert(cls, file, name, printer_id, status): 
        try:
            job = cls(
                file=file,
                name=name,
                printer_id=printer_id,
                status=status,
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
        return self.file
    
    def getStatus(self): 
        return self.status 
    
    def getPrinterId(self): 
        return self.printer_id
    
    def setStatus(self, status): 
        self.status = status