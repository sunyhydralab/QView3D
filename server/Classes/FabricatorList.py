import serial.tools.list_ports
from flask import jsonify
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS

from Classes.Fabricators.Device import Device
from Classes.Ports import Ports
from Classes.Fabricators.Fabricator import Fabricator

class FabricatorList():
    fabricators: [Fabricator] = []
    @staticmethod
    def __iter__():
        return iter(FabricatorList.fabricators)

    @staticmethod
    def __len__():
        return len(FabricatorList.fabricators)

    @staticmethod
    def init():
        """initialize the list of printers"""
        FabricatorList.fabricators = Fabricator.queryAll()

    @staticmethod
    def addFabricator(serialPortName: str, name: str = ""):
        """add a printer to the list, and to the database"""
        serialPort: ListPortInfo | SysFS | None = Ports.getPortByName(serialPortName)
        # TODO: check if the fabricator is in the db
        dbFab: Fabricator | None = next((fabricator for fabricator in Fabricator.queryAll() if fabricator.hwid == serialPort.hwid.split(' LOCATION=')[0]), None)
        listFab: Fabricator | None = next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getHwid() == serialPort.hwid.split(' LOCATION=')[0]), None)
        if dbFab is not None: # means that the fabricator is in the db
            if listFab is not None: # means that the fabricator is in the list and the db
                print("Fabricator is already in the list and the db")
            else: # means that the fabricator is in the db but not in the list
                FabricatorList.fabricators.append(Fabricator(serialPort, name=dbFab.getname()))
        else: # means that the fabricator is not in the db
            if listFab is not None: # means that the fabricator is in the list but not in the db
                listFab.addToDB()
            else: # means that the fabricator is not in the list or the db
                FabricatorList.fabricators.append(Fabricator(serialPort, name=name, addToDB=True))

        # TODO: check that printerlist and database are in sync
        dbPrinters = Fabricator.queryAll()
        assert(len(FabricatorList.fabricators) == len(dbPrinters))
        assert all(printer in FabricatorList.fabricators for printer in dbPrinters)

    @staticmethod
    def deleteFabricator(printerid):
        """delete a printer from the list, and from the database"""
        # TODO: Implement deleteFabricator
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
    def getFabricatorByName(name) -> Fabricator | None:
        """find the first printer with the given name"""
        return next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getName() == name), None)

    @staticmethod
    def getPrinterByHwid(hwid) -> Fabricator | None:
        """find the first printer with the given hwid"""
        return next((fabricator for fabricator in FabricatorList.fabricators if fabricator.getHwid() == hwid), None)

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
    
    