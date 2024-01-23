from flask import Blueprint, jsonify, request, make_response

# get data for jobs 
jobs_bp = Blueprint("jobs", __name__)