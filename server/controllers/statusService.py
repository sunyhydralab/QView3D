# API for user communication to printer threads 
from flask import Blueprint
 
status_bp = Blueprint("status", __name__)

@status_bp.route('/ping', methods=["GET"])
def getStatus(Printer):
    pass

@status_bp.route('/getopenthreads')
def getOpenThreads():
    pass 