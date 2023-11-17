from flask import Blueprint, render_template
from Classes import serialCommunication
from Classes.Printer import Printer 
from flask import request
import requests 
from tasks.main import create_job
# from flask import requests as rq

display_bp = Blueprint('display', __name__)

@display_bp.route("/")
def main():
    return render_template("nav.html")

@display_bp.route('/selectport')
def selectPort():
    # printerlist = Printer.getSupportedPrinters()
    printerlist = serialCommunication.get3DPrinterList()
    return render_template("selectport.html", printerlist=printerlist)

@display_bp.route('/botselected', methods=['POST'])
def botSelected(): 
    selected_port = request.form.get('ports')
    file = request.form.get('file')
    quantity = request.form.get('quantity')
    priority = request.form.get('priority')
    
    if(priority == "on"): 
        priority = 1 
    else: 
        priority = 0 
        
    create_job(file, "test", quantity, priority, selected_port, 1)
    return render_template("botselected.html", selected_port = selected_port)



