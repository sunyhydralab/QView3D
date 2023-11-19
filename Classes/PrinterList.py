from Classes.Printer import Printer
class PrinterList: 
    
    def __init__(self, printerlist): 
        self.__list = []
        for port in printerlist: 
            self.addPrinter(port)
          
    def addPrinter(self, port): # add printer to printer list 
        printer = Printer(port, None, False) # port, filament, virtual
        self.__list.append(printer)
        
    def autoQueue(self): # Get index of printer with smallest queue 
        minIndex = 0 
        for index, printer in enumerate(self.__list): 
            size = printer.getSizeOfQueue()
            if size < self.__list[minIndex].getSizeOfQueue(): 
                minIndex = index 
        return minIndex 
            
        
            
        
        
    