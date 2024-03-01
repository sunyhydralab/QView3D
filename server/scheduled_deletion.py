from app import app
from flask import current_app
import schedule
import time
from datetime import datetime, timedelta

def job():
    with app.app_context():
        # six_months_ago = datetime.now() - timedelta(days=6*30)  # Approximation of 6 months
        one_minute_ago = datetime.now() - timedelta(minutes=1)  # 1 minute ago

        # Assuming you have a Job model with a date field and a file field
        # old_jobs = Job.query.filter(Job.date < six_months_ago).all()
        
        old_jobs = Job.query.filter(Job.date < one_minute_ago).all()

        for job in old_jobs:
            job.file = None  # Set file to None
        db.session.commit()  # Commit the changes

# Schedule the job every 6 months
schedule.every(6).months.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)