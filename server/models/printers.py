from models.db import db 
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.exc import SQLAlchemyError
from flask import jsonify 

# model for Printer table 
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(50), nullable=False)
    hwid = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False) 
    
    def __init__(self, device, description, hwid, name, status):
        self.device = device
        self.description = description 
        self.hwid = hwid 
        self.name = name 
        self.status = status
    
    @classmethod
    def searchByDevice(cls, device): 
        try:
            # Query the database to find a printer by device
            printer = cls.query.filter_by(device=device).first()
            return printer is not None
        
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None
        
    @classmethod    
    def create_printer(cls, device, description, hwid, name, status): 
        printerExists = cls.searchByDevice(device)
        if printerExists: 
            return {"success": False, "message": "Printer already registered."}
        else: 
            printer = cls(device=device, description=description, hwid=hwid, name=name, status=status)
            db.session.add(printer)
            db.session.commit()
            return {"success": True, "message": "Printer successfully registered."}


