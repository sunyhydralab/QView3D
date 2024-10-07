from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError
import serial
import serial.tools.list_ports
from Classes.Device import Device
from Classes.Ports import Ports
from Classes.Printer import Printer

class PrinterList():
    printers = Printer.queryAll()

    @staticmethod
    def addPrinter(serialPortName: str, name: str):
        """add a printer to the list, and to the database"""
        # TODO: test if the printer is already in the list
        serialPort = Ports.getPortByName(serialPortName)
        if PrinterList.getPrinterByHwid(serialPort.hwid):
            return None # TODO: return error message
        PrinterList.printers.append(Printer(Device.createDevice(serialPort), name))
        # TODO: check that printerlist and database are in sync
        dbPrinters = Printer.queryAll()
        if len(PrinterList.printers) != len(dbPrinters):
            return None # TODO: return error message
        for printer in dbPrinters:
            if printer not in PrinterList.printers:
                return None # TODO: return error message

    @staticmethod
    def deletePrinter(printerid):
        """delete a printer from the list, and from the database"""
        # TODO: Implement deletePrinter
        pass
        # try:
        #     ports = serial.tools.list_ports.comports()
        #     for port in ports:
        #         hwid = port["hwid"]  # get hwid
        #         if hwid == Printer.query.get(printerid).hwid:
        #             ser = serial.Serial(port["device"], 115200, timeout=1)
        #             ser.close()
        #             break
        #     printer = PrinterList.query.get(printerid)
        #     db.session.delete(printer)
        #     db.session.commit()
        #     return {"success": True, "message": "Printer successfully deleted."}
        # except SQLAlchemyError as e:
        #     print(f"Database error: {e}")
        #     return (
        #         jsonify({"error": "Failed to delete printer. Database error"}),
        #         500,
        #     )
    @staticmethod
    def getPrinterCount():
        return len(PrinterList.printers)

    @staticmethod
    def getPrinterByName(name) -> Printer | None:
        """find the first printer with the given name"""
        for printer in PrinterList.printers:
            if printer.get_name() == name:
                return printer
        return None

    @staticmethod
    def getPrinterByHwid(hwid) -> Printer | None:
        """find the first printer with the given hwid"""
        for printer in PrinterList.printers:
            if printer.get_hwid() == hwid:
                return printer
        return None
    
    