from io import BytesIO
from flask import Blueprint, jsonify, request, make_response
from models.jobs import Job
from app import printer_status_service
import json 
from werkzeug.utils import secure_filename
import os 
# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs(): 
    try:
        res = Job.get_job_history()
        # since response isn't iterable, we need to convert it to a JSON object
        return jsonify({"jobs": res})
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# add job to queue
@jobs_bp.route('/addjobtoqueue', methods=["POST"])
def add_job_to_queue():
    try:
        file = request.files['file']  # Access file directly from request.files
        file_name = file.filename
        name = request.form['name']  # Access other form fields from request.form
        printerid = int(request.form['printerid'])

        job = Job(file, name, printerid, file_name=file_name) # create job object 
        
        threads = printer_status_service.getThreadArray()
        
        printerobject = list(filter(lambda thread: thread.printer.id == printerid, threads))[0].printer
        
        printerobject.getQueue().addToBack(job)
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# route to insert job into database
@jobs_bp.route('/jobdbinsert', methods=["POST"])
def job_db_insert():
    try:
        jobdata = request.form.get('jobdata')
        
        jobdata = json.loads(jobdata)  # Convert jobdata from JSON to a Python dictionary

        # Get the individual fields from jobdata
        name = jobdata.get('name')
        printer_id = jobdata.get('printer_id')
        status = jobdata.get('status')
        file_name=jobdata.get("file_name")
        file_path=jobdata.get("file_path")

        # Insert the job data into the database
        res = Job.jobHistoryInsert(name, printer_id, status, file_name, file_path)

        # print(name, printer_id, status)
        return "success"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/rerunjob', methods=["POST"])
def rerun_job():
    try:
        data = request.get_json()

        printerid = data['id']
        file_name = data['job']['file_name']
        job_name = data['job']['name']

        job = Job(file=None, name=job_name, printer_id=printerid, file_name=file_name) # create job object without passing file.
        
        threads = printer_status_service.getThreadArray()
        
        printerobject = list(filter(lambda thread: thread.printer.id == printerid, threads))[0].printer
        
        printerobject.getQueue().addToBack(job)
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/deletejob', methods=["POST"])
def remove_job():
    try:
        # job has: printer id. job info.
        data = request.get_json()
        status = data['status']
        printer_id = data['printerid']
        job_id = data['job_id']
        file_name=data['file_name']
        name = data['name']
        
        file_path = Job.generatePath(file_name)
    
        threads = printer_status_service.getThreadArray()
        printerobject = list(filter(lambda thread: thread.printer.id == printer_id, threads))[0].printer # get printer job is queued to 
        queue = printerobject.getQueue()
        
        job = queue.deleteJob(job_id) # retrieve and remove job from queue
        Job.deleteFile(file_path) # delete file from folder
        
        job.setStatus("cancelled") # set status of job to cancelled.

        if status == "printing":
            printerobject.setStatus("complete")
            printerobject.stopPrint()
            Job.jobHistoryInsert(name, printer_id, "cancelled", file_name, file_path)
            pass 

        return jsonify({"success": True, "message": "Job removed from printer queue."}), 200

        # check status of job. 
            # if job is not printing: 
                # set job status to cancelled.
                # remove from queue 
                # remove file from folder 
                
            # if job is printing: 
                # Send GCODE command to stop printer. 
                # printer status = "complete." 
                # wait for user intervention to set to "ready."
                # Job status = cancelled. 
                # remove job from queue 
                # Insert job into DB. 
                # remove file from folder 
        # 

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500