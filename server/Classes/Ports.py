import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from Classes.Fabricators.Fabricator import Fabricator
from Classes.serialCommunication import sendGcode
from app import current_app as app
from Classes.FabricatorConnection import EmuListPortInfo

class Ports:
    @staticmethod
    def getPorts():
        """Get a list of all connected serial ports."""
        ports = serial.tools.list_ports.comports()
        emu_port, emu_name, emu_hwid = app.get_emu_ports()
        if emu_port and emu_name and emu_hwid:
            ports.append(EmuListPortInfo(emu_port, description="Emulator", hwid=emu_hwid))
        # if app:
        #     if app.fabricator_list is not None:
        #         print(1)
        #         [print(fab.device) for fab in app.fabricator_list.fabricators]
        #     else:
        #         print("No fabricator list")
        full_devices = []
        for port in ports:
            if app:
                if app.fabricator_list.getFabricatorByPort(port) is None:
                    if port.device == emu_port:
                        device = Fabricator.staticCreateDevice(port, websocket_connection=next(iter(app.emulator_connections.values())))
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
        return serial.tools.list_ports.comports()

    @staticmethod
    def getPortByName(name: str):
        """Get a specific port by its device name."""
        assert isinstance(name, str), f"Name must be a string: {name} : {type(name)}"
        ports = Ports.getListPorts()
        emu_port, emu_name, emu_hwid = app.get_emu_ports()
        if emu_port and emu_name and emu_hwid:
            ports.append(EmuListPortInfo(emu_port, description="Emulator", hwid=emu_hwid))
        for port in ports:
            if not port: continue
            if port.device == name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str):
        """Get a specific port by its hardware ID."""
        assert isinstance(hwid, str), f"HWID must be a string: {hwid} : {type(hwid)}"
        ports = Ports.getListPorts()
        for port in ports:
            if hwid in port.hwid:
                return port
        return None

    @staticmethod
    def getRegisteredFabricators() -> list[Fabricator]:
        """Get a list of all registered fabricators."""
        fabricators = Fabricator.queryAll()
        registered_fabricators = []
        for fab in fabricators:
            port = Ports.getPortByName(fab.devicePort)
            if port:
                registered_fabricators.append(fab)
        return registered_fabricators

    @staticmethod
    def diagnosePort(port: ListPortInfo | SysFS) -> str:
        """Diagnose a port to check if it is functional by sending basic G-code commands."""
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