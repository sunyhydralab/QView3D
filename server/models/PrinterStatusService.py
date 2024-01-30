from threading import Thread
from models.printers import Printer
import serial
import serial.tools.list_ports
import time 
class PrinterStatusService:
    def __init__(self):
        self.printer_threads = [] # array of printer threads
        self.ping_thread = None 

    def start_printer_thread(self, printer):
        thread = Thread(target=self.update_thread, args=(printer,)) 
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        # all printer statuses intiialized to be 'online.' Instantly changes to 'ready' on initialization -- test with 'reset printer' command.
        for printer_info in printers_data:
            printer = Printer(
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
            )
            printer_thread = self.start_printer_thread(printer) # creating a thread for each printer object 
            self.printer_threads.append(printer_thread)
        
        # creating seperate thread to loop through all of the printer threads to ping them for print status  
        self.ping_thread = Thread(target = self.pingForStatus)

    
    def update_thread(self, printer): 
        while True: 
            status = printer.getStatus()
            if status == 'online':
                printer.initialize() # code to change status from online -> ready on thread start 
            
            queueSize = printer.getQueue().getSize()
            if status == "ready" and queueSize > 0: 
                printer.printNextInQueue()
                
    def pingForStatus(self): 
        pass 
    
    
    def getThreadArray(self): 
        return self.printer_threads