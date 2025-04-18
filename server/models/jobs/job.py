from db import get_db
from datetime import datetime
from typing import Dict

def create_job(data: Dict, filename: str):
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
            INSERT INTO Jobs (
                name, 
                gcode_file_name, 
                status, 
                date_create, 
                date_completed, 
                is_favorite, 
                ticket_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            )''', (
                    data['name'],
                    filename,
                    data['status'],
                    data['date_created'],
                    data['date_completed'],
                    int(data['is_favorite']),
                    data['ticket_id']
                ))
    job_id = cursor.lastrowid
    db.commit()
    return job_id