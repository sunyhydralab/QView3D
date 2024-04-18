import base64
from io import BytesIO
import io
import shutil
import tempfile
from flask import Blueprint, Response, jsonify, request, make_response, send_file
from models.jobs import Job
from models.printers import Printer
from app import printer_status_service
import json 
from werkzeug.utils import secure_filename
import os 
import gzip
from flask import current_app
import serial
import serial.tools.list_ports

# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs():
    page = request.args.get('page', default=1, type=int)
    pageSize = request.args.get('pageSize', default=10, type=int)
    printerIds = request.args.get('printerIds', type=json.loads)
    
    oldestFirst = request.args.get('oldestFirst', default='false')
    oldestFirst = oldestFirst.lower() in ['true', '1']

    searchJob = request.args.get('searchJob', default='', type=str)
    searchCriteria = request.args.get('searchCriteria', default='', type=str)

    favoriteOnly = request.args.get('favoriteOnly', default='false')
    favoriteOnly = favoriteOnly.lower() in ['true', '1']
    
    try:
        res = Job.get_job_history(page, pageSize, printerIds, oldestFirst, searchJob, searchCriteria, favoriteOnly)
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/geterrorjobs', methods=["GET"])
def getErrorJobs():
    page = request.args.get('page', default=1, type=int)
    pageSize = request.args.get('pageSize', default=10, type=int)
    printerIds = request.args.get('printerIds', type=json.loads)
    searchJob = request.args.get('searchJob', default='', type=str)
    issueIds = request.args.get('issueIds', type=json.loads)
    
    oldestFirst = request.args.get('oldestFirst', default='false')
    oldestFirst = oldestFirst.lower() in ['true', '1']

    searchCriteria = request.args.get('searchCriteria', default='', type=str)
    
    try:
        res = Job.get_job_error_history(page, pageSize, printerIds, oldestFirst, searchJob, searchCriteria, issueIds)
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

# add job to queue
@jobs_bp.route('/addjobtoqueue', methods=["POST"])
def add_job_to_queue():
    try:
        # retrieve job data 
        file = request.files['file']  # Access file directly from request.files
        file_name_original = file.filename
        name = request.form['name']  # Access other form fields from request.form
        printer_id = int(request.form['printerid'])
        favorite = request.form['favorite']
        # favorite = 1 if _favorite == 'true' else 0
        quantity = request.form['quantity']
        td_id = int(request.form['td_id'])
        favoriteOne = False 

        for i in range(int(quantity)):
            if(favorite == 'true' and not favoriteOne):
                favorite = 1
                favoriteOne = True
            else: 
                favorite = 0
                
            status = 'inqueue' # set status 
            res = Job.jobHistoryInsert(name, printer_id, status, file, file_name_original, favorite, td_id) # insert into DB 
            
            # retrieve job from DB
            id = res['id']
            
            job = Job.query.get(id)
            
            base_name, extension = os.path.splitext(file_name_original)

            # Append the ID to the base name
            file_name_pk = f"{base_name}_{id}{extension}"
            
            job.setFileName(file_name_pk) # set unique in-memory file name 

            priority = request.form['priority']
            # if priotiry is '1' then add to front of queue, else add to back
            if priority == 'true':
                findPrinterObject(printer_id).getQueue().addToFront(job, printer_id)
            else:
                findPrinterObject(printer_id).getQueue().addToBack(job, printer_id)
                        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/autoqueue', methods=["POST"])
def auto_queue(): 
    try: 
        file = request.files['file']  # Access file directly from request.files
        file_name_original = file.filename
        name = request.form['name']  # Access other form fields from request.form
        quantity = request.form['quantity']

        favorite = request.form['favorite']
        td_id = request.form['td_id']

        favoriteOne = False 
        for i in range(int(quantity)):
            status = 'inqueue' # set status 
            printer_id = getSmallestQueue()
            
            if(favorite == 'true' and not favoriteOne):
                favorite = 1
                favoriteOne = True
            else: 
                favorite = 0
            # favorite = 1 if _favorite == 'true' else 0
            
            res = Job.jobHistoryInsert(name, printer_id, status, file, file_name_original, favorite, td_id) # insert into DB 
            
            id = res['id']
            
            job = Job.query.get(id)
            
            base_name, extension = os.path.splitext(file_name_original)

            # Append the ID to the base name
            file_name_pk = f"{base_name}_{id}{extension}"
            
            job.setFileName(file_name_pk) # set unique in-memory file name 

            findPrinterObject(printer_id).getQueue().addToBack(job, printer_id)  
        
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route('/rerunjob', methods=["POST"])
def rerun_job():
    try:
        data = request.get_json()
        printerpk = data['printerpk'] # printer to rerun job on 
        jobpk = data['jobpk']
        
        rerunjob(printerpk, jobpk, "back")
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
        # file_name=jobdata.get("file_name")
        file_path=jobdata.get("file_path")

        # Insert the job data into the database
        res = Job.jobHistoryInsert(name, printer_id, status, file_path)

        return "success"
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
 
 # cancel queued job   
@jobs_bp.route('/canceljob', methods=["POST"]) 
def remove_job():
    try:
        # job has: printer id. job info.
        # 0 = cancel job, 1 = clear job, 2 = fail job, 3 = clear job (but also rerun)
        data = request.get_json()
        jobpk = data['jobpk']
        # Retrieve job to delete & printer id 
        job = Job.findJob(jobpk) 
        printerid = job.getPrinterId() 

        jobstatus = job.getStatus()
        # retrieve printer object & corresponding queue
        printerobject = findPrinterObject(printerid)
        # printerobject.setStatus("complete")
        queue = printerobject.getQueue()
        inmemjob = queue.getJob(job)
        if jobstatus == 'printing': # only change statuses, dont remove from queue 
            printerobject.setStatus("complete")
        else: 
            queue.deleteJob(jobpk, printerid) 
            
        inmemjob.setStatus("cancelled")
        Job.update_job_status(jobpk, "cancelled")

        return jsonify({"success": True, "message": "Job removed from printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    

 # cancel queued job   
@jobs_bp.route('/cancelfromqueue', methods=["POST"]) 
def remove_job_from_queue():
    try:
        # job has: printer id. job info.
        # 0 = cancel job, 1 = clear job, 2 = fail job, 3 = clear job (but also rerun)
        data = request.get_json()
        jobarr = data['jobarr']
        
        for jobpk in jobarr:
            # Retrieve job to delete & printer id 
            job = Job.findJob(jobpk) 
            printerid = job.getPrinterId() 

            jobstatus = job.getStatus()
            # retrieve printer object & corresponding queue
            printerobject = findPrinterObject(printerid)
            # printerobject.setStatus("complete")
            queue = printerobject.getQueue()
            inmemjob = queue.getJob(job)
            if jobstatus == 'printing': # only change statuses, dont remove from queue 
                printerobject.setStatus("complete")
            else: 
                queue.deleteJob(jobpk, printerid) 
                
            inmemjob.setStatus("cancelled")
            Job.update_job_status(jobpk, "cancelled")

        return jsonify({"success": True, "message": "Job removed from printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
    
@jobs_bp.route('/releasejob', methods=["POST"])
def releasejob(): 
    try: 
        data = request.get_json()
        jobpk = data['jobpk']
        key = data['key']
        job = Job.findJob(jobpk) 
        printerid = job.getPrinterId() 
        printerobject = findPrinterObject(printerid)
        printerobject.error = ""
        queue = printerobject.getQueue()

        queue.deleteJob(jobpk, printerid) # remove job from queue
        
        printerid = data['printerid']
        
        currentStatus = printerobject.getStatus()

        if key == 3: 
            Job.update_job_status(jobpk, "error")
            printerobject.setError(job.comments)
            printerobject.setStatus("error") # printer ready to accept new prints 
            
        elif key == 2: 
            rerunjob(printerid, jobpk, "front")
            
            if currentStatus!="offline":
                printerobject.setStatus("ready") # printer ready to accept new prints 
                
        elif key == 1: 
            if currentStatus!="offline":
                printerobject.setStatus("ready") # printer ready to accept new prints 
            
        return jsonify({"success": True, "message": "Job released successfully."}), 200
    
    except Exception as e: 
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500  
    
@jobs_bp.route('/bumpjob', methods=["POST"])
def bumpjob():
    try:
        data = request.get_json()
        printer_id = data['printerid']
        job_id = data['jobid']
        choice = data['choice']
        
        printerobject = findPrinterObject(printer_id)
        
        if choice == 1: 
            printerobject.queue.bump(True, job_id)
        elif choice == 2: 
            printerobject.queue.bump(False, job_id)
        elif choice == 3: 
            printerobject.queue.bumpExtreme(True, job_id, printer_id)
        elif choice == 4: 
            printerobject.queue.bumpExtreme(False, job_id, printer_id)
        else: 
            return jsonify({"error": "Unexpected error occurred"}), 500
        
        return jsonify({"success": True, "message": "Job bumped up in printer queue."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/movejob', methods=["POST"])
def moveJob():
    try:
        data = request.get_json()
        printer_id = data['printerid']
        arr = data['arr']
        
        printerobject = findPrinterObject(printer_id)
        printerobject.queue.reorder(arr)
        return jsonify({"success": True, "message": "Queue updated successfully."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500   
    
@jobs_bp.route('/updatejobstatus', methods=["POST"])
def updateJobStatus():
    try:
        data = request.get_json()
        job_id = data['jobid']
        newstatus = data['status']
        
        res = Job.update_job_status(job_id, newstatus)
        
        job = Job.findJob(job_id) 
        printerid = job.getPrinterId() 
        printerobject = findPrinterObject(printerid)
        queue = printerobject.getQueue()
        
        # queue.deleteJob(job_id, printerid)
        
        return jsonify(res), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/assigntoerror', methods=["POST"])
def assignToError():
    try:
        data = request.get_json()
        job_id = data['jobid']
        newstatus = data['status']
        
        res = Job.update_job_status(job_id, newstatus)
        
        job = Job.findJob(job_id) 
        printerid = job.getPrinterId() 
        printerobject = findPrinterObject(printerid)
        queue = printerobject.getQueue()
        
        queue.deleteJob(job_id, printerid)
        
        return jsonify(res), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/deletejob', methods=["POST"])
def delete_job():
    try:
        data = request.get_json()
        job_id = data['jobid']
        
        # Retrieve job to delete & printer id 
        job = Job.findJob(job_id) 
        printer_id = job.getPrinterId() 
        print("ID: ", printer_id)
        
        if printer_id != 0:
            # Retrieve printer object & corresponding queue
            printer_object = findPrinterObject(printer_id)
            queue = printer_object.getQueue()
            
            # Delete job from the queue
            queue.deleteJob(job_id, printer_id) 

            # Delete job from the database
        Job.delete_job(job_id)

        return jsonify({"success": True, "message": f"Job with ID {job_id} deleted successfully."}), 200

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route("/setstatus", methods=["POST"])
def setStatus():
    try:
        data = request.get_json() # get json data 
        printer_id = data['printerid']
        newstatus = data['status']
 
        printerobject = findPrinterObject(printer_id)
        
        printerobject.setStatus(newstatus)
        
        return jsonify({"success": True, "message": "Status updated successfully."}), 200

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route('/getfile', methods=["GET"])
def getFile():
    try:
        job_id = request.args.get('jobid', default=-1, type=int)        
        job = Job.findJob(job_id) 
        file_blob = job.getFile()  # Assuming this returns the file blob
        decompressed_file = gzip.decompress(file_blob).decode('utf-8')
        
        return jsonify({"file": decompressed_file, "file_name": job.getFileNameOriginal()}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/nullifyjobs', methods=["POST"])
def nullifyJobs():
    try: 
        data = request.get_json()
        printerid = data['printerid']
        res = Job.nullifyPrinterId(printerid)
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/clearspace', methods=["GET"])
def clearSpace(): 
    try: 
        res = Job.clearSpace()
        return res 
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/getfavoritejobs', methods=["GET"])
def getFavoriteJobs():
    try:
        res = Job.getFavoriteJobs()
        return jsonify(res)
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/favoritejob', methods=["POST"])
def favoriteJob():
    try: 
        data = request.get_json()
        jobid = data['jobid']
        favorite = data['favorite']
        job = Job.findJob(jobid)
        res = job.setFileFavorite(favorite)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/assignissue', methods=["POST"])
def assignIssue():
    try: 
        data = request.get_json()
        jobid = data['jobid']
        issueid = data['issueid']
        job = Job.findJob(jobid)
        jobid = job.getJobId()
        res = job.setIssue(jobid, issueid)
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/startprint', methods=["POST"])
def startPrint(): 
    try: 
        data = request.get_json()
        printerid = data['printerid']
        jobid = data['jobid']
        printerobject = findPrinterObject(printerid)
        queue = printerobject.getQueue()
        inmemjob = queue.getJobById(jobid)
        print(inmemjob)
        inmemjob.setReleased(1)
        
        return jsonify({"success": True, "message": "Job started successfully."}), 200
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected ersetupPortRepairSocketror occurred"}), 500
    
@jobs_bp.route('/savecomment', methods=["POST"])
def saveComment(): 
    try: 
        data = request.get_json()
        jobid = data['jobid']
        comment = data['comment']
        
        # job = Job.findJob(jobid)
        res = Job.setComment(jobid, comment)
        return res 
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
@jobs_bp.route('/downloadcsv', methods=["GET"])
def downloadCSV():
    try:
        res = Job.downloadCSV()
        return res
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500

@jobs_bp.route("/repairports", methods=["POST", "GET"])
def repair_ports(): 
    try:
        ports = serial.tools.list_ports.comports()    
        print("PORTS: ", ports)
        for port in ports: 
            hwid = port.hwid # get hwid 
            hwid_without_location = hwid.split(' LOCATION=')[0]
            printer = Printer.getPrinterByHwid(hwid_without_location)
            if printer is not None: 
                if(printer.getDevice()!=port.device):
                    printer.editPort(printer.getId(), port.device)
                    printerthread = findPrinterObject(printer.getId())
                    printerthread.setDevice(port.device)
        return {"success": True, "message": "Printer port(s) successfully updated."}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error occurred"}), 500
    
    
def findPrinterObject(printer_id): 
    threads = printer_status_service.getThreadArray()
    return list(filter(lambda thread: thread.printer.id == printer_id, threads))[0].printer  

def getSmallestQueue():
    threads = printer_status_service.getThreadArray()
    smallest_queue_thread = min(threads, key=lambda thread: thread.printer.queue.getSize())
    return smallest_queue_thread.printer.id
    
def rerunjob(printerpk, jobpk, position):
    job = Job.findJob(jobpk) # retrieve Job to rerun 
    
    status = 'inqueue' # set status 
    file_name_original = job.getFileNameOriginal() # get original file name
    favorite = job.getFileFavorite() # get favorite status
    td_id = job.getTdId() 
    # Insert new job into DB and return new PK 
    res = Job.jobHistoryInsert(name=job.getName(), printer_id=printerpk, status=status, file=job.getFile(), file_name_original=file_name_original, favorite = favorite, td_id=td_id) # insert into DB 
    
    id = res['id']
    file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique
    
    rjob = Job.query.get(id)
    
    base_name, extension = os.path.splitext(file_name_original)

    # Append the ID to the base name
    file_name_pk = f"{base_name}_{id}{extension}"
    
    rjob.setFileName(file_name_pk) # set unique file name 
    
    if position == "back":
        findPrinterObject(printerpk).getQueue().addToBack(rjob, rjob.printer_id)
    else: 
        findPrinterObject(printerpk).getQueue().addToFront(rjob, rjob.printer_id)
        