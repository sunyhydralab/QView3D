from flask import Blueprint, jsonify, request, make_response

# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)

@jobs_bp.route('/getjobs', methods=["GET"])
def getJobs(): 
    pass 