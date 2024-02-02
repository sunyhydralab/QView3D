from io import BytesIO
from flask import Blueprint, jsonify, request, make_response
from models.jobs import Job
from app import printer_status_service
import json 
# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs(): 
    try:
        res = Job.get_job_history()
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# add job to queue
@jobs_bp.route('/addjobtoqueue', methods=["POST"])
def add_job_to_queue():
    try:
        file = request.files['file']  # Access file directly from request.files
        name = request.form['name']  # Access other form fields from request.form
        printerid = int(request.form['printerid'])
        print(file)
        
        # Read the file contents into memory
        file_contents = BytesIO(file.read())
        
        # job = Job(file, name, printerid)
        job = Job(file_contents, name, printerid)
        threads = printer_status_service.getThreadArray()
        
        print(threads)
        printerobject = list(filter(lambda thread: thread.printer.id == printerid, threads))[0].printer
        
        printerobject.getQueue().addToBack(job)
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500