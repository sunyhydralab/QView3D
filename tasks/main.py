import sys
import os
import threading
import queue
from flask import Blueprint
from Classes.Printer import Printer 
from Classes.Job import Job

main = Blueprint('main', __name__)

def create_job(file, name, quantity, priority, port, status):
    from app import printerObjects # get cached printer objects 
    
    # Generating job with file, name, quantity, priority, status. 
    test_job = Job(file, name, quantity, priority, status)
    
    if(port == "None"): # OPTION FOR IF YOU WANT TO PRINT TO PRINTER W/ SMALLEST QUEUE: 
        # select printer with smallest queue. Add to queue of specific printer and also database 
        sortedPrinterList = printerObjects.autoQueue() # returns a dict sorted by which printer has smallest queue
        nextPrinter = sortedPrinterList[0][1] # gets printer object. tuple is in form (mongoId: PrinterObject)
        handleQueue(nextPrinter, test_job)
        printer_util(nextPrinter, test_job)
    else: 
        # PRINT TO SPECIFIC PRINTER: 
        for _port, _printerobj in printerObjects.getList(): 
            if _port == port: 
                handleQueue(_printerobj, test_job)
                printer_util(_printerobj, test_job)
                break 
        else: 
            print("Error")
        # print to specific printer, add to specific queue and also database 

# add job to queue, add job to queue in mongoDB database 
def printer_util(printer, job): #isAuto: False if specific port, True if port not specified 
    #printer = Printer(selected_port, None, True) # Creating Printer object with selected port 
    printer.connect()  # Connect to the printer
    printer.reset()    # Reset the printer
    printer.printJob(job)  # Send the job to the printer
    printer.disconnect()        # Disconnect from the printer
        
def handleQueue(printer, job): 
    from app import printers # printers is a collection in MongoDB
    # from app import printerObjects # get cached printer objects 
    printer.addToQueue(job) # adding to queue on this end. Have some separation mechanism - atomic operations? 
    # make it so the database / in-memory insertion is separate. Then have a way to consistently loop through all printers 
    # in-memory and  print next to queue. When printer is finished recieve GCode command. 
    
    # also add to DB queue: 
    database_printer = printers.find_one({'_id': printer.getId()})
    printer_id = printer.getId() # mongodb ID stored in-memory
    if database_printer:
        # Use atomic update with $push to add job to the queue
        printers.update_one(
            {'_id': printer_id},
            {'$push': {'queue': job.file}}
        )
    else:
        # Handle the case where the printer is not found in the database
        print(f"Printer with ID {printer_id} not found in the database.")
     
        