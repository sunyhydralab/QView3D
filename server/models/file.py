from models.db import db

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file = db.Column(db.LargeBinary(16777215), nullable=True)
    
    def __init__(self, file):
        self.file = file
    