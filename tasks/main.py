from flask import Blueprint, render_template
from Classes import serialCommunication
from Classes.Printer import Printer 
from flask import request 
from Classes.Job import Job

main = Blueprint('main', __name__)

def create_job(file, name, quantity, priority, port):
    test_job = Job(file, name, quantity, priority)
    printer_util(port, test_job)

def printer_util(selected_port, job):
    if selected_port:
        # Basic structure of sending a job to the printer.
        printer = Printer(selected_port)  # Create a Printer object.
        printer.connect()  # Connect to the printer.
        printer.reset()  # Reset the printer.
        printer.printJob(job)  # Send the job to the printer.
        printer.reset()  # Reset the printer.
        printer.disconnect()  # Disconnect from the printer.
    else:
        print("No supported printers found.")