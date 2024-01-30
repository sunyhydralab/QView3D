from threading import Thread
from models.printers import Printer

# this is the thread class that will be used to create a thread for each printer
class PrinterThread(Thread):
    def __init__(self, printer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.printer = printer
        
class PrinterStatusService:
    def __init__(self):
        self.printer_threads = [] # array of printer threads

    def start_printer_thread(self, printer):
        thread = PrinterThread(printer, target=self.update_thread, args=(printer,)) # temporary lock 
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        for printer_info in printers_data:
            printer = Printer(
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
                status="ready",
            )
            printer_thread = self.start_printer_thread(printer) # creating a thread for each printer object 
            self.printer_threads.append(printer_thread)
    
    # this method will be called by the UI to get the printers that have a threads information
    def retrieve_printer_info(self):
        printer_info_list = []
        for thread in self.printer_threads:
            printer = thread.printer  # get the printer object associated with the thread
            printer_info = {
                "device": printer.device,
                "description": printer.description,
                "hwid": printer.hwid,
                "name": printer.name,
                "status": printer.status,
            }
            printer_info_list.append(printer_info)
        return printer_info_list
        
        
    def update_thread(self, printer):
        """_summary_

        This is the thread's target function. This function can call other functions. 
        This is where we will be pinging for status and updating the printer passed to this 
        function. Do not worry about the Printer object mapped to the threads -- this is simply a 
        simple way for us as the programmers to map the printer info to the associated threads to 
        display status and such. 
        
        The threading is a way to constantly get the status of the printer and update it on the UI. 
        
            
        """
        pass 