from models.db import db 
from datetime import datetime
from sqlalchemy import Column, String, LargeBinary, DateTime, ForeignKey
from sqlalchemy.orm import relationship

# model for Printer table 
class Printer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    port = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  
