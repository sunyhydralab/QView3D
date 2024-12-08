import shutil
from flask import Blueprint, jsonify, request
from Classes.Jobs import Job
from models.db import db
from models.printers import Printer
import json
import os 
import gzip
import serial
import serial.tools.list_ports
from globals import current_app
from traceback import format_exc
from Classes.Fabricators.Fabricator import Fabricator

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
    
    searchTicketId = request.args.get('searchTicketId', default='', type=str)

    favoriteOnly = request.args.get('favoriteOnly', default='false')
    favoriteOnly = favoriteOnly.lower() in ['true', '1']
    
    issueIds = request.args.get('issueIds', type=json.loads)
    
    startdate = request.args.get('startdate', default='', type=str)
    enddate = request.args.get('enddate', default='', type=str)
    
    fromError = request.args.get('fromError', default=0, type=int)
    
    countOnly = request.args.get('countOnly', default=0, type=int)

    try:
        res = Job.get_job_history(page, pageSize, printerIds, oldestFirst, searchJob, searchCriteria, searchTicketId, favoriteOnly, issueIds, startdate, enddate, fromError, countOnly)
        return jsonify(res)
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        # quantity = request.form['quantity']
        td_id = int(request.form['td_id'])
        filament = request.form['filament']
        favoriteOne = False

        # for i in range(int(quantity)):
        if favorite == 'true' and not favoriteOne:
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

        job.setFilament(filament) # set filament type

        priority = request.form['priority']
        # if priotiry is '1' then add to front of queue, else add to back
        fabricator = findPrinterObject(printer_id)
        if fabricator is None:
            return jsonify({"error": "Fabricator not found."}), 404
        if priority == 'true':
            fabricator.queue.addToFront(job, printer_id)
        else:
            fabricator.queue.addToBack(job, printer_id)

        return jsonify({"success": True, "message": "Job added to printer queue."}), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/autoqueue', methods=["POST"])
def auto_queue():
    try:
        file = request.files['file']  # Access file directly from request.files
        file_name_original = file.filename
        name = request.form['name']  # Access other form fields from request.form
        # quantity = request.form['quantity']

        favorite = request.form['favorite']
        td_id = request.form['td_id']
        filament = request.form['filament']

        favoriteOne = False
        # for i in range(int(quantity)):
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

        job.setFilament(filament) # set filament type
        fabricator = findPrinterObject(printer_id)
        if fabricator is None:
            return jsonify({"error": "Fabricator not found."}), 404
        fabricator.queue.addToBack(job, printer_id)
        return jsonify({"success": True, "message": "Job added to printer queue."}), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/rerunjob', methods=["POST"])
def rerun_job():
    try:
        data = request.get_json()
        printerpk = data['printerpk'] # printer to rerun job on
        jobpk = data['jobpk']

        return rerunjob(printerpk, jobpk, "back")
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        res = Job.jobHistoryInsert(name, printer_id, status, file_path, file_name)

        return "success"
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        if printerobject is None:
            return jsonify({"error": "Fabricator not found."}), 404
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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500


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
            if printerobject is None:
                return jsonify({"error": "Fabricator not found."}), 404
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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500


@jobs_bp.route('/releasejob', methods=["POST"])
def releasejob():
    if request.method != "POST":
        return
    try:
        data = request.get_json()
        jobpk = data['jobpk']
        key = data['key']
        job = Job.findJob(jobpk)
        printerid = job.getPrinterId()
        fabricator = findPrinterObject(printerid)
        if fabricator is None:
            return jsonify({"error": "Printer not found."}), 404
        print(fabricator)
        fabricator.error = ""
        if len(fabricator.queue) > 0:
            assert len(fabricator.queue) > 0, "Queue is empty"
            assert fabricator.queue[0].getJobId() == jobpk, "Job not at front of queue"
            fabricator.queue.removeJob()
        if fabricator.job is not None:
            fabricator.job = None

        printerid = data['printerid']

        currentStatus = fabricator.getStatus()

        if key == 3:
            Job.update_job_status(jobpk, "error")
            fabricator.setError(job.comments)
            fabricator.setStatus("error") # printer ready to accept new prints

        elif key == 2:

            if currentStatus!="offline":
                fabricator.setStatus("ready") # printer ready to accept new prints

            return rerunjob(printerid, jobpk, "front")

        elif key == 1:
            if currentStatus!="offline":
                fabricator.setStatus("ready") # printer ready to accept new prints
                
        if current_app:
            db.session.commit()

        return jsonify({"success": True, "message": "Job released successfully."}), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/bumpjob', methods=["POST"])
def bumpjob():
    try:
        data = request.get_json()
        printer_id = data['printerid']
        job_id = data['jobid']
        choice = data['choice']

        printerobject = findPrinterObject(printer_id)
        if printerobject is None:
            return jsonify({"error": "Fabricator not found"}), 404

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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/movejob', methods=["POST"])
def moveJob():
    try:
        data = request.get_json()
        printer_id = data['printerid']
        arr = data['arr']

        printerobject = findPrinterObject(printer_id)
        if printerobject is None:
            return jsonify({"error": "Fabricator not found"}), 404
        printerobject.queue.reorder(arr)
        return jsonify({"success": True, "message": "Queue updated successfully."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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

        queue.deleteJob(job_id, printerid)

        return jsonify(res), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        if printerobject is not None:
            queue = printerobject.getQueue()
            queue.deleteJob(job_id, printerid)

        return jsonify(res), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/deletejob', methods=["POST"])
def delete_job():
    try:
        data = request.get_json()
        job_id = data['jobid']

        # Retrieve job to delete & printer id
        job = Job.findJob(job_id)
        printer_id = job.getPrinterId()

        if printer_id != 0:
            # Retrieve printer object & corresponding queue
            printer_object = findPrinterObject(printer_id)
            if printer_object is not None:
                queue = printer_object.getQueue()

                # Delete job from the queue
                queue.deleteJob(job_id, printer_id)

        # Delete job from the database
        Job.delete_job(job_id)

        return jsonify({"success": True, "message": f"Job with ID {job_id} deleted successfully."}), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/setstatus", methods=["POST"])
def setStatus():
    try:
        data = request.get_json() # get json data
        printer_id = data['printerid']
        newStatus = data['status']
        fabricator: Fabricator | None = findPrinterObject(printer_id)
        if fabricator is not None:
            fabricator.setStatus(newStatus)
            return jsonify({"success": True, "message": "Status updated successfully."}), 200
        else:
            print(f"Fabricator not found: {printer_id}, fabricator: {fabricator}")
            return jsonify({"error": "Printer not found."}), 404
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/getfile', methods=["GET"])
def getFile():
    try:
        job_id = request.args.get('jobid', default=-1, type=int)
        job = Job.findJob(job_id)
        file_blob = job.getFile()  # Assuming this returns the file blob
        decompressed_file = gzip.decompress(file_blob).decode('utf-8')

        return jsonify({"file": decompressed_file, "file_name": job.getFileNameOriginal()}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/nullifyjobs', methods=["POST"])
def nullifyJobs():
    try:
        data = request.get_json()
        printerid = data['printerid']
        res = Job.nullifyPrinterId(printerid)
        return res
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/clearspace', methods=["GET"])
def clearSpace():
    try:
        res = Job.clearSpace()
        return res
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/getfavoritejobs', methods=["GET"])
def getFavoriteJobs():
    try:
        res = Job.getFavoriteJobs()
        return jsonify(res)
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/removeissue', methods=["POST"])
def removeIssue():
    try:
        data = request.get_json()
        jobid = data['jobid']
        job = Job.findJob(jobid)
        jobid = job.getJobId()
        res = job.unsetIssue(jobid)
        return res
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/startprint', methods=["POST"])
def startPrint():
    try:
        data = request.get_json()
        printerid = data['printerid']
        jobid = data['jobid']
        printerobject = findPrinterObject(printerid)
        queue = printerobject.getQueue()
        assert queue is not None, "Queue not found."
        printerobject.job = queue.getJobById(jobid)
        assert printerobject.job is not None, "Job not found."
        if printerobject.job.getStatus() == "inqueue": printerobject.job.setStatus("ready")
        assert printerobject.job.getStatus() == "ready", f"Job not ready to print. Status: {printerobject.job.getStatus()}"
        assert printerobject.job == queue[0], "Job not at front of queue."
        printerobject.job.setReleased(1)
        printerobject.setStatus("printing")


        return jsonify({"success": True, "message": "Job started successfully."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/savecomment', methods=["POST"])
def saveComment():
    try:
        data = request.get_json()
        jobid = data['jobid']
        comments = data['comments']

        # job = Job.findJob(jobid)
        res = Job.setComment(jobid, comments)
        return res

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/downloadcsv', methods=["GET", "POST"])
def downloadCSV():
    try:
        data = request.get_json()
        alljobsselected = data.get('allJobs')
        jobids = data.get('jobIds')

        if alljobsselected == 1:
            # Call the model method to get the CSV content
            res = Job.downloadCSV(1)
        else:
            # Call the model method to get the CSV content
            res = Job.downloadCSV(0, jobids)
        return res

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/removeCSV', methods=["GET", "POST"])
def removeCSV():
    try:
        # Create in-memory uploads folder
        csv_folder = os.path.join('../tempcsv')
        if os.path.exists(csv_folder):
            shutil.rmtree(csv_folder)
            os.makedirs(csv_folder)
            print("TempCSV folder recreated as an empty directory.")
        else:
            # Create the uploads folder if it doesn't exist
            os.makedirs(csv_folder)
            print("TempCSV folder created successfully.")

        return jsonify({"success": True, "message": "CSV file removed successfully."}), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/repairports", methods=["POST", "GET"])
def repair_ports():
    try:
        ports = serial.tools.list_ports.comports()
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
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/refetchtimedata", methods=['POST', 'GET'])
def refetch_time():
    try:
        data = request.get_json()
        jobid = data['jobid']
        printerid = data['printerid']

        printer = findPrinterObject(printerid)
        if printer is None:
            return jsonify({"error": "Fabricator not found"}), 404
        job = printer.getQueue().getNext()
        if job is None:
            return jsonify({"error": "No job found"}), 404

        timearray = job.job_time

        timejson = {
            'total': timearray[0],
            'eta': timearray[1].isoformat(),
            'timestart': timearray[2].isoformat(),
            'pause': timearray[3].isoformat()
        }

        return jsonify(timejson), 200

    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

def findPrinterObject(fabricator_id):
    """
    Find the printer object by its ID.
    :param fabricator_id: The ID of the printer.
    :type fabricator_id: int
    :rtype: Fabricator | None
    """
    threads = current_app.fabricator_list.getThreadArray()
    print(threads)
    fabricatorThread = list(filter(lambda thread: thread.fabricator.dbID == fabricator_id, threads))
    return fabricatorThread[0].fabricator if len(fabricatorThread) > 0 else None

def getSmallestQueue():
    threads = current_app.fabricator_list.getThreadArray()
    smallest_queue_thread = min(threads, key=lambda thread: len(thread.fabricator.queue))
    return smallest_queue_thread.fabricator.dbID

def rerunjob(printerpk, jobpk, position):
    job = Job.findJob(jobpk) # retrieve Job to rerun

    status = 'inqueue' # set status
    file_name_original = job.getFileNameOriginal() # get original file name
    favorite = job.getFileFavorite() # get favorite status
    td_id = job.getTdId()
    # Insert new job into DB and return new PK
    res = Job.jobHistoryInsert(name=job.getName(), fabricator_id=printerpk, status=status, file=job.getFile(), file_name_original=file_name_original, favorite=favorite, td_id=td_id) # insert into DB

    id = res['id']
    file_name_pk = file_name_original + f"_{id}" # append id to file name to make it unique

    rjob = Job.query.get(id)

    base_name, extension = os.path.splitext(file_name_original)

    # Append the ID to the base name
    file_name_pk = f"{base_name}_{id}{extension}"

    rjob.setFileName(file_name_pk) # set unique file name
    fabricator = findPrinterObject(printerpk)
    if fabricator is None:
        return jsonify({"error": "Fabricator not found."}), 404
    if position == "back":
        findPrinterObject(printerpk).getQueue().addToBack(rjob, rjob.fabricator_id)
    else:
        findPrinterObject(printerpk).getQueue().addToFront(rjob, rjob.fabricator_id)

    return jsonify({"success": True, "message": "Job added to printer queue."}), 200
