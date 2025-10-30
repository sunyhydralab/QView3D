import shutil
from flask import Blueprint, jsonify, request, Response
from Classes.Jobs import Job
from config.db import db
import json
import os
import gzip
import serial.tools.list_ports
from services.app_service import current_app
from traceback import format_exc
from Classes.Fabricators.Fabricator import Fabricator
from Classes.Fabricators.Printers.Printer import Printer

jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs():
    page = request.args.get('page', default=1, type=int)
    pageSize = request.args.get('pageSize', default=10, type=int)
    printerIds = request.args.get('printerIds', type=json.loads)
    oldestFirst = request.args.get('oldestFirst', default='false').lower() in ['true', '1']
    searchJob = request.args.get('searchJob', default='', type=str)
    searchCriteria = request.args.get('searchCriteria', default='', type=str)
    searchTicketId = request.args.get('searchTicketId', default='', type=str)
    favoriteOnly = request.args.get('favoriteOnly', default='false').lower() in ['true', '1']
    issueIds = request.args.get('issueIds', type=json.loads)
    startdate = request.args.get('startdate', default='', type=str)
    enddate = request.args.get('enddate', default='', type=str)
    fromError = request.args.get('fromError', default=0, type=int)
    countOnly = request.args.get('countOnly', default=0, type=int)

    try:
        res = Job.get_job_history(page, pageSize, printerIds, oldestFirst, searchJob, searchCriteria, searchTicketId, favoriteOnly, issueIds, startdate, enddate, fromError, countOnly)
        if countOnly == 0:
            jobs_data, total = res
            return jsonify({"jobs": jobs_data, "total": total})
        else:
            return jsonify({"total": res})
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/addjobtoqueue', methods=["POST"])
def add_job_to_queue():
    try:
        file = request.files['file']
        file_name_original = file.filename
        name = request.form['name']
        printer_id = int(request.form['printerid'])
        favorite = 1 if request.form['favorite'] == 'true' else 0
        td_id = int(request.form['td_id'])
        filament = request.form['filament']

        res = Job.jobHistoryInsert(name, printer_id, 'submitted', file, file_name_original, favorite, td_id)
        id = res['id']
        job = Job.query.get(id)

        base_name, extension = os.path.splitext(file_name_original)
        file_name_pk = f"{base_name}_{id}{extension}"
        job.setFileName(file_name_pk)
        job.setFilament(filament)

        fabricator = findPrinterObject(printer_id)
        if fabricator is None:
            return jsonify({"error": "Fabricator not found."}), 404

        if request.form['priority'] == 'true':
            fabricator.queue.addToFront(job)
        else:
            fabricator.queue.addToBack(job)

        return jsonify({"success": True, "message": "Job added to printer queue."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/autoqueue', methods=["POST"])
def auto_queue():
    try:
        file = request.files['file']
        file_name_original = file.filename
        name = request.form['name']
        favorite = 1 if request.form['favorite'] == 'true' else 0
        td_id = request.form['td_id']
        filament = request.form['filament']

        fabricator_id = getSmallestQueue()
        res = Job.jobHistoryInsert(name, fabricator_id, 'submitted', file, file_name_original, favorite, td_id)
        id = res['id']
        job = Job.query.get(id)

        base_name, extension = os.path.splitext(file_name_original)
        file_name_pk = f"{base_name}_{id}{extension}"
        job.setFileName(file_name_pk)
        job.setFilament(filament)

        fabricator = findPrinterObject(fabricator_id)
        if fabricator is None:
            return jsonify({"error": "Fabricator not found."}), 404
        fabricator.queue.addToBack(job)
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

@jobs_bp.route('/jobdbinsert', methods=["POST"])
def job_db_insert():
    try:
        jobdata = json.loads(request.form.get('jobdata'))
        res = Job.jobHistoryInsert(jobdata.get('name'), jobdata.get('printer_id'), jobdata.get('status'), jobdata.get('file_path'), jobdata.get('file_name'))
        return "success"
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/canceljob', methods=["POST"])
def remove_job():
    try:
        data = request.get_json()
        jobpk = data['jobpk']
        job = Job.findJob(jobpk)
        printerid = job.getPrinterId()
        jobstatus = job.getStatus()

        printerobject = findPrinterObject(printerid)
        if printerobject is None:
            return jsonify({"error": "Fabricator not found."}), 404

        queue = printerobject.getQueue()
        inmemjob = queue.getJob(job)

        if jobstatus == 'printing':
            printerobject.setStatus("complete")
        else:
            queue.deleteJob(jobpk, printerid)

        inmemjob.setStatus("cancelled")
        Job.update_job_status(jobpk, "cancelled")

        return jsonify({"success": True, "message": "Job removed from printer queue."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/cancelfromqueue', methods=["POST"])
def remove_job_from_queue():
    try:
        data = request.get_json()
        jobarr = data['jobarr']
        errors = []
        success_count = 0

        for jobpk in jobarr:
            try:
                job = Job.findJob(jobpk)
                if not job:
                    errors.append(f"Job {jobpk} not found")
                    continue

                printerid = job.getPrinterId()
                jobstatus = job.getStatus()
                printerobject = findPrinterObject(printerid)
                if printerobject is None:
                    errors.append(f"Fabricator not found for job {jobpk}")
                    continue

                queue = printerobject.getQueue()
                inmemjob = queue.getJob(job)

                if jobstatus == 'printing':
                    printerobject.setStatus("complete")
                else:
                    queue.deleteJob(jobpk, printerid)

                if inmemjob:
                    inmemjob.setStatus("cancelled")
                Job.update_job_status(jobpk, "cancelled")
                success_count += 1
            except Exception as e:
                errors.append(f"Failed to cancel job {jobpk}: {str(e)}")
                continue

        if errors and success_count == 0:
            return jsonify({"error": "All jobs failed to cancel", "details": errors}), 500
        elif errors:
            return jsonify({"success": True, "message": f"{success_count} job(s) cancelled", "warnings": errors}), 200
        else:
            return jsonify({"success": True, "message": "Job(s) removed from printer queue."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500


@jobs_bp.route('/releasejob', methods=["POST"])
def releasejob():
    try:
        data = request.get_json()
        jobpk = data['jobpk']
        key = data['key']
        printerid = data['printerid']

        job = Job.findJob(jobpk)
        fabricator = findPrinterObject(printerid)
        if fabricator is None:
            return jsonify({"error": "Printer not found."}), 404

        fabricator.error = ""
        if len(fabricator.queue) > 0:
            assert fabricator.queue[0].getJobId() == jobpk, "Job not at front of queue"
            fabricator.queue.removeJob()

        currentStatus = fabricator.getStatus()

        if key == 3:
            Job.update_job_status(jobpk, "error")
            fabricator.setStatus("ready")
            if current_app:
                current_app.socketio.emit("fabricator_status_update", {"id": printerid, "status": "ready"})
        elif key == 2:
            if currentStatus != "offline":
                fabricator.setStatus("ready")
                if current_app:
                    current_app.socketio.emit("fabricator_status_update", {"id": printerid, "status": "ready"})
            return rerunjob(printerid, jobpk, "front")
        elif key == 1:
            if currentStatus != "offline":
                fabricator.setStatus("ready")
                if current_app:
                    current_app.socketio.emit("fabricator_status_update", {"id": printerid, "status": "ready"})

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

@jobs_bp.route('/reorderqueue', methods=["POST"])
def reorderQueue():
    try:
        data = request.get_json()
        fabricator_id = data.get('fabricator_id')
        job_ids = data.get('job_ids')

        if not fabricator_id or not job_ids:
            return jsonify({"error": "fabricator_id and job_ids are required"}), 400

        printerobject = findPrinterObject(fabricator_id)
        if printerobject is None:
            return jsonify({"error": "Fabricator not found"}), 404

        printerobject.queue.reorder(job_ids)
        return jsonify({"success": True, "message": "Queue reordered successfully."}), 200
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
        job = Job.findJob(job_id)
        printer_id = job.getPrinterId()

        if printer_id != 0:
            printer_object = findPrinterObject(printer_id)
            if printer_object is not None:
                printer_object.getQueue().deleteJob(job_id, printer_id)

        Job.delete_job(job_id)
        return jsonify({"success": True, "message": f"Job with ID {job_id} deleted successfully."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/setstatus", methods=["POST"])
def setStatus():
    try:
        data = request.get_json() # get json data
        printer_id = data['id']
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
        file_blob = job.getFile()
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

        if printerobject is None:
            return jsonify({"error": "Fabricator not found."}), 404

        queue = printerobject.getQueue()
        assert queue is not None, "Queue not found."
        assert len(queue) > 0, f"Queue is empty for printer {printerid}"
        assert printerobject.queue[0] is not None, f"Job not found: jobid: {jobid}"

        job = printerobject.queue[0]
        # Change status from 'submitted' to 'inqueue' to trigger auto-start
        if job.getStatus() == "submitted":
            job.setStatus("inqueue")
            Job.update_job_status(job.id, "inqueue")
        assert job.getStatus() in ["inqueue", "ready"], f"Job not ready to print. Status: {job.getStatus()}"

        # Start the print job directly
        current_app.fabricator_list.start_print_job(printerobject, job)
        return jsonify({"success": True, "message": "Job started successfully."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/confirmjobcomplete', methods=["POST"])
def confirmJobComplete():
    """
    Manually confirm that a printed job is complete.
    Called when user clicks the Complete button after inspecting the print.
    """
    try:
        data = request.get_json()
        printerid = data['printerid']
        jobid = data['jobid']

        printerobject = findPrinterObject(printerid)
        if printerobject is None:
            return jsonify({"error": "Fabricator not found."}), 404

        queue = printerobject.getQueue()
        if queue is None or len(queue) == 0:
            return jsonify({"error": "No job in queue."}), 404

        job = queue[0]
        if job.id != jobid:
            return jsonify({"error": f"Job mismatch. Expected {jobid}, found {job.id}"}), 400

        # Verify job is in awaiting confirmation state
        if job.status != 'awaiting_user_confirmation':
            return jsonify({"error": f"Job not awaiting confirmation. Status: {job.status}"}), 400

        # Mark job as complete
        job.status = 'complete'
        Job.update_job_status(jobid, 'complete')

        # Remove from queue
        queue.removeJob()
        print(f"Job {jobid} manually marked complete and removed from queue")

        # Set fabricator back to ready
        printerobject.status = 'ready'

        return jsonify({"success": True, "message": "Job marked as complete."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/savecomment', methods=["POST"])
def saveComment():
    try:
        data = request.get_json()
        res = Job.setComment(data['jobid'], data['comments'])
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
        res = Job.downloadCSV(1) if alljobsselected == 1 else Job.downloadCSV(0, jobids)
        return res
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route('/removeCSV', methods=["GET", "POST"])
def removeCSV():
    try:
        csv_folder = os.path.join('../tempcsv')
        if os.path.exists(csv_folder):
            shutil.rmtree(csv_folder)
        os.makedirs(csv_folder)
        return jsonify({"success": True, "message": "CSV file removed successfully."}), 200
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/repairports", methods=["POST", "GET"])
def repair_ports():
    try:
        ports = serial.tools.list_ports.comports()
        repaired_fabricators = []

        for port in ports:
            hwid_without_location = port.hwid.split(' LOCATION=')[0]
            printer = Printer.getPrinterByHwid(hwid_without_location)
            if printer is not None and printer.getDevice() != port.device:
                printer.editPort(printer.getId(), port.device)
                printerthread = findPrinterObject(printer.getId())
                printerthread.setDevice(port.device)
                repaired_fabricators.append({
                    'fabricator_id': printer.getId(),
                    'Fabricator': printer.__to_JSON__()
                })

        if current_app.socketio and repaired_fabricators:
            for fabricator_info in repaired_fabricators:
                current_app.socketio.emit('port_repair', fabricator_info)

        return {"success": True, "message": "Printer port(s) successfully updated."}
    except Exception as e:
        current_app.handle_errors_and_logging(e)
        return jsonify({"error": format_exc()}), 500

@jobs_bp.route("/refetchtimedata", methods=['POST', 'GET'])
def refetch_time():
    try:
        data = request.get_json()
        printer = findPrinterObject(data['printerid'])
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

def findPrinterObject(fabricator_id: int) -> Fabricator | None:
    fabricators = current_app.fabricator_list.fabricators
    for fabricator in fabricators:
        if fabricator.dbID == fabricator_id:
            return fabricator
    return None

def getSmallestQueue() -> int:
    all_fabricators = current_app.fabricator_list.fabricators
    if len(all_fabricators) == 0:
        raise Exception("No fabricators available")
    smallest_queue_fabricator = min(all_fabricators, key=lambda fab: len(fab.queue))
    return smallest_queue_fabricator.dbID

def rerunjob(printerpk: int, jobpk: int, position: str) -> tuple[Response, int]:
    job = Job.findJob(jobpk)
    file_name_original = job.getFileNameOriginal()
    res = Job.jobHistoryInsert(name=job.getName(), fabricator_id=printerpk, status='submitted', file=job.getFile(), file_name_original=file_name_original, favorite=job.getFileFavorite(), td_id=job.getTdId())

    id = res['id']
    rjob = Job.query.get(id)
    base_name, extension = os.path.splitext(file_name_original)
    file_name_pk = f"{base_name}_{id}{extension}"
    rjob.setFileName(file_name_pk)

    fabricator = findPrinterObject(printerpk)
    if fabricator is None:
        return jsonify({"error": "Fabricator not found."}), 404

    if position == "back":
        fabricator.getQueue().addToBack(rjob)
    else:
        fabricator.getQueue().addToFront(rjob)

    return jsonify({"success": True, "message": "Job added to printer queue."}), 200
