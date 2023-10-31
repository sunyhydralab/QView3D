from flask import Blueprint, render_template
from Classes import serialCommunication
from flask import request 

display_bp = Blueprint('display', __name__)

@display_bp.route("/")
def main():
    return render_template("nav.html")

@display_bp.route('/selectport')
def selectPort():
    printerlist = serialCommunication.get3DPrinterList()
    return render_template("selectport.html", printerlist=printerlist)

@display_bp.route('/botselected', methods=['POST'])
def botSelected(): 
    selected_port = request.form.get('ports')
    return render_template("botselected.html", selected_port = selected_port)



