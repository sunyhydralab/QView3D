from threading import Thread
from models.printers import Printer

class PrinterStatusService:
    def __init__(self):
        self.printer_threads = [] # array of printer threads

    def start_printer_thread(self, printer):
        thread = Thread(target=self.update_thread, args=(printer,)) # temporary lock 
        thread.start()
        return thread

    def create_printer_threads(self, printers_data):
        for printer_info in printers_data:
            printer = Printer(
                device=printer_info["device"],
                description=printer_info["description"],
                hwid=printer_info["hwid"],
                name=printer_info["name"],
                status = 'ready'
            )
            printer_thread = self.start_printer_thread(printer) # creating a thread for each printer object 
            self.printer_threads.append(printer_thread)
            # self.printer_threads[printer] = printer_thread # mapping printer object to printer thread 

        
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