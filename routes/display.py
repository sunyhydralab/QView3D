from flask import Blueprint, render_template
from Classes import serialCommunication
from Classes.Printer import Printer 
from flask import request
import requests 
from tasks.main import create_job

display_bp = Blueprint('display', __name__)

@display_bp.route("/")
def main():
    return render_template("nav.html")

@display_bp.route('/selectport')
def selectPort():
    from app import printers # import printer collection 
    # Retrieve ports of all registered printers from MongoDB
    cursor = printers.find({}, {'_id': 0, 'port': 1})
    printerlist = [doc['port'] for doc in cursor] # filtering so it only displays port.device 
    
    printerlist = serialCommunication.get3DPrinterList() # retrieve list of supported printers 
    if len(printerlist) > 0: 
        return render_template("selectport.html", printerlist=printerlist)
    else: 
        return "Error"

@display_bp.route('/botselected', methods=['POST'])
def botSelected(): 
    
    # retrieving selected printer, file, quantity, and priority. 
    selected_port = request.form.get('ports')
    file = request.form.get('file')
    quantity = request.form.get('quantity')
    priority = request.form.get('priority')
    
    if(priority == "on"): 
        priority = 1 
    else: 
        priority = 0 
    
    # creating a job with the selected port. 
    create_job(file, "test", quantity, priority, selected_port, 1)
    return render_template("botselected.html", selected_port = selected_port)



