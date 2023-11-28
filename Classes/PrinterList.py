from Classes.Printer import Printer
class PrinterList: 
    
    def __init__(self): 
        self.__list = {} # Stores mongodbid: Printer Object 
          
    def addPrinter(self, port, id): # add printer to printer list 
        printer = Printer(port, id, None, True) # port, filament, virtual
        # self.__list.append(printer)
        self.__list[id] = printer 
        
    def autoQueue(self): # Get index of printer with smallest queue 
        # sort printer objects by size of queue 
        sortPrintersByQueueSize = sorted(self.__list.items(), key=lambda item: item[1].getSizeOfQueue())
        return sortPrintersByQueueSize # returns a list of tuples

    def getList(self): 
        return self.__list; 
            
        
            
        
        
    