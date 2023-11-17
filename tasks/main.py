import sys
import os
import threading
import queue
from flask import Blueprint
from Classes.Printer import Printer 
from Classes.Job import Job

main = Blueprint('main', __name__)

def create_job(file, name, quantity, priority, port, status):
    serial_printers = 1 # 0 for real printers 
    
    # Have system: map specific ports to specific names. 1 = this port, 2 = other port, etc. 
    if serial_printers == 0:
        available_printers = Printer.getSupportedPrinters(virtual=False)
    elif serial_printers == 1:
        available_printers = Printer.getSupportedPrinters(virtual=True)

    if not available_printers:
        print("No supported printers found.")
        exit()
        
    # # Selecting the first available printer for demonstration
    # selected_printer = available_printers[0]
    
    # Create a Job - assuming you have a Job class
    test_job = Job(file, name, quantity, priority, status)
    
    # This just selects the first printer in the list.  Replace this with the queue.
    printer_util(port, test_job)

def printer_util(selected_port, job):
    if selected_port:
        printer = Printer(selected_port, None, True)
        
        printer.connect()  # Connect to the printer
        printer.reset()    # Reset the printer
        printer.printJob(job)  # Send the job to the printer
        printer.disconnect()        # Disconnect from the printer
        
    else:
        print("No supported printers found.")