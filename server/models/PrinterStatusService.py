from threading import Thread
from models.printers import Printer

class PrinterStatusService:
    def __init__(self):
        self.printer_threads = {}

    def start_printer_thread(self, printer):
        thread = Thread(target=self.getStatus, args=(printer,)) # temporary lock 
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        for printer_info in printers_data:
            printer = Printer(
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
            )
            printer_thread = self.start_printer_thread(printer) # creating a thread for each printer object 
            self.printer_threads[printer] = printer_thread # mapping printer object to printer thread 

        
    def getStatus(self, printer):
        print(printer.getStatus())