import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from Classes.Fabricators.Fabricator import Fabricator
from Classes.serialCommunication import sendGcode
from globals import current_app as app
from Classes.FabricatorConnection import EmuListPortInfo

class Ports:
    @staticmethod
    def getPorts() -> list[dict]:
        """
        Get a list of all connected serial ports in JSON format
        :rtype: list[dict]
        """
        ports = serial.tools.list_ports.comports()
        emu_port, emu_name, emu_hwid = app.get_emu_ports()
        if emu_port and emu_name and emu_hwid:
            ports.append(EmuListPortInfo(emu_port, description="Emulator", hwid=emu_hwid))
        full_devices = []
        for port in ports:
            if app:
                if app.fabricator_list.getFabricatorByPort(port) is None:
                    if port.device == emu_port:
                        values = app.emulator_connections.values()
                        ws = next(iter(values), None)
                        device = Fabricator.staticCreateDevice(port, websocket_connection=ws)
                    else:
                        device = Fabricator.staticCreateDevice(port)
                    full_devices.append(device)
            else:
                full_devices.append(Fabricator(port).device)
        devices = [{
            "device": device.__to_JSON__(),
            "hwid": device.getHWID(),
            "description": device.DESCRIPTION
        } for device in full_devices if device is not None]
        return devices

    @staticmethod
    def getListPorts():
        """
        Get a list of all connected serial ports.
        :rtype: list[ListPortInfo | SysFS]
        """
        return serial.tools.list_ports.comports()

    @staticmethod
    def getPortByName(name: str):
        """
        Get a specific port by its device name.
        :param name: The name of the device.
        :type name: str
        :return: The port object
        :rtype: ListPortInfo | SysFS
        """
        assert isinstance(name, str), f"Name must be a string: {name} : {type(name)}"
        ports = Ports.getListPorts()
        if len(app.emulator_connections) > 0:
            emu_port, emu_name, emu_hwid = app.get_emu_ports()
            if emu_port and emu_name and emu_hwid and emu_port == name:
                return EmuListPortInfo(emu_port, description="Emulator", hwid=emu_hwid)
        for port in ports:
            if not port: continue
            if port.device.strip("/").split("/")[-1] in name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str):
        """
        Get a specific port by its hardware ID.
        :param str hwid: The hardware ID of the device.
        :rtype: ListPortInfo | SysFS | None
        """
        assert isinstance(hwid, str), f"HWID must be a string: {hwid} : {type(hwid)}"
        ports = Ports.getListPorts()
        for port in ports:
            if hwid in port.hwid:
                return port
        return None

    @staticmethod
    def getRegisteredFabricators():
        """
        Get a list of all registered fabricators.
        :rtype: list[Fabricator]
        """
        fabricators = Fabricator.queryAll()
        registered_fabricators = []
        for fab in fabricators:
            port = Ports.getPortByName(fab.devicePort)
            if port:
                registered_fabricators.append(fab)
        return registered_fabricators

    @staticmethod
    def diagnosePort(port: ListPortInfo | SysFS) -> str:
        """
        Diagnose a port to check if it is functional by sending basic G-code commands.
        :param ListPortInfo | SysFS port: The port to diagnose
        :rtype: str
        """
        try:
            if app:
                device = app.fabricator_list.getFabricatorByPort(port).device
            else:
                device = Fabricator(port).device
            if not device:
                return "Device creation failed."

            device.connect()
            sendGcode("M115")
            response = device.getSerialConnection().readline().decode("utf-8").strip()
            device.disconnect()

            return f"Diagnosis result for {port.device}: {response}"
        except Exception as e:
            return f"Error diagnosing port {port.device}: {e}"