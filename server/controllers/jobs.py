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
        
        # Read the file contents into memory. QUESTION: WILL THIS WORK FOR LARGE FILES? WILL THIS OVERLOAD THE MEMORY? 
        # file_contents = BytesIO(file.read())
        
        # Save the file to the server
        Job.saveToFolder(file)

        job = Job(file, name, printerid, file_name=file_name)
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
        # Get the file from the request files
        file = request.files['file']
        file_contents = file.read()

        # Get the job data from the request
        jobdata = request.form.get('jobdata')
        jobdata = json.loads(jobdata)  # Convert jobdata from JSON to a Python dictionary

        # Get the individual fields from jobdata
        name = jobdata.get('name')
        printer_id = jobdata.get('printer_id')
        status = jobdata.get('status')
        file_name=jobdata.get('file_name')

        # Insert the job data into the database
        res = Job.jobHistoryInsert(file_contents, name, printer_id, status, file_name)
        
        del file_contents  # Delete the file contents from memory

        # print(name, printer_id, status)
        return "success"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500