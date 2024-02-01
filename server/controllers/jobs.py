from flask import Blueprint, jsonify, request, make_response
from models.jobs import Job
from app import printer_status_service

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
        data = request.get_json()
        file = data["file"]
        name = data["name"]
        # status = data["status"]
        # date = data["date"]
        printerid= data["printerid"]
        
        job = Job(file, name, printerid)
        threads = printer_status_service.getThreadArray()
        printerobject = list(filter(lambda thread: thread.printer.id == printerid, threads))[0].printer
        
        printerobject.getQueue().addToBack(job)
        
        # print(printerobject.getQueue().getNext().getName())
        # set job status once in queue 
        
        # job = Job.create_job(file, name, status, date, printer)
        # printer_status_service.add_job_to_printer_queue(job)
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500