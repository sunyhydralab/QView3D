import serial.tools.list_ports
from flask import jsonify

from Classes.Fabricators.Device import Device
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator

class FabricatorList():
    fabricators = Fabricator.queryAll()
    @staticmethod
    def __iter__():
        return iter(FabricatorList.fabricators)

    @staticmethod
    def addFabricator(serialPortName: str, name: str):
        """add a printer to the list, and to the database"""
        # TODO: test if the printer is already in the list
        serialPort = Ports.getPortByName(serialPortName)
        if FabricatorList.getPrinterByHwid(serialPort.hwid):
            return None # TODO: return error message
        FabricatorList.fabricators.append(Fabricator(Device.createDevice(serialPort), name))
        # TODO: check that printerlist and database are in sync
        dbPrinters = Fabricator.queryAll()
        if len(FabricatorList.fabricators) != len(dbPrinters):
            return None # TODO: return error message
        for printer in dbPrinters:
            if printer not in FabricatorList.fabricators:
                return None # TODO: return error message

    @staticmethod
    def deleteFabricator(printerid):
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
    def getFabricatorCount():
        return len(FabricatorList.fabricators)

    @staticmethod
    def getFabricatorByName(name) -> Fabricator | None:
        """find the first printer with the given name"""
        for fabricator in FabricatorList.__iter__():
            if fabricator.getName() == name:
                return fabricator
        return None

    @staticmethod
    def getPrinterByHwid(hwid) -> Fabricator | None:
        """find the first printer with the given hwid"""
        for fabricator in FabricatorList.__iter__():
            if fabricator.getHwid() == hwid:
                return fabricator
        return None

    @staticmethod
    def diagnose(device: Device):
        try:
            diagnoseString = ""
            for port in serial.tools.list_ports.comports():
                if port.device == device.getSerialPort().device:
                    diagnoseString += f"The system has found a <b>matching port</b> with the following details: <br><br> <b>Device:</b> {port.device}, <br> <b>Description:</b> {port.description}, <br> <b>HWID:</b> {port.hwid}"
                    hwid = device.getHWID()
                    printerExists = FabricatorList.getPrinterByHwid(hwid)
                    if printerExists:
                        printer = FabricatorList.getPrinterByHwid(hwid)
                        diagnoseString += f"<hr><br>Device <b>{port.device}</b> is registered with the following details: <br><br> <b>Name:</b> {printer.name} <br> <b>Device:</b> {printer.device}, <br> <b>Description:</b> {printer.description}, <br><b> HWID:</b> {printer.hwid}"
            if diagnoseString == "":
                diagnoseString = "The port this printer is registered under is <b>not found</b>. Please check the connection and try again."
            # return diagnoseString
            return {
                "success": True,
                "message": "Printer successfully diagnosed.",
                "diagnoseString": diagnoseString,
            }

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500
    
    