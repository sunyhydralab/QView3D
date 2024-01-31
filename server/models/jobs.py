from models.db import db 
from datetime import datetime
from models.printers import Printer
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from flask import jsonify 
from sqlalchemy.exc import SQLAlchemyError
import uuid

# model for job history table 
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary, nullable=False)
    name = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
    
    # foreign key relationship to match jobs to the printer printed on 
    printer_id = db.Column(db.Integer, db.ForeignKey('printer.id'), nullable = False)
    printer = db.relationship('Printer', backref='Job')
    
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
        
    # method to create a new job
    @classmethod
    def create_job(cls, file, name, status, date, printer_name):
        # print all the printers names in the database
        printers = Printer.query.all()
        for printer in printers:
            if printer.name == printer_name:
                # create a new job object
                job = cls(id=cls.generate_unique_id(), file=file, name=name, status=status, date=date, printer=printer)
        return job
    
    # method to generate a unique id for the job
    # can change later, not sure if we even need this
    @staticmethod
    def generate_unique_id():
        # generate a unique ID
        # this is a placeholder implementation, replace it with your actual implementation
        return uuid.uuid4().int & (1<<32)-1