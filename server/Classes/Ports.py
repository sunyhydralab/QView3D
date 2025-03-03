import re

import serial
import serial.tools.list_ports
from serial.tools.list_ports_common import ListPortInfo
from serial.tools.list_ports_linux import SysFS
from pyvisa.resources.resource import Resource
from Classes.Fabricators.Fabricator import Fabricator
from Classes.MyPyVISA.CustomTCPIPInstrument import EmuTCPIPInstrument
from Classes.serialCommunication import sendGcode
from globals import current_app as app
from globals import system_device_prefix

class Ports:
    @staticmethod
    def getPorts() -> list[dict]:
        """
        Get a list of all connected serial ports in JSON format
        :rtype: list[dict]
        """
        ports_str = Ports.getListPorts()
        print(f"Ports strings: {ports_str}")
        ports = [app.resource_manager.open_resource(port) for port in ports_str]
        print(f"Ports: {ports}")
        emu_port, emu_name, emu_hwid = app.get_emu_ports()
        #TODO: make the emu class a subclass of Resource instead of ListPortInfo
        if emu_port and emu_name and emu_hwid:
            ports.append(EmuTCPIPInstrument(app.resource_manager, emu_port, description="Emulator", hwid=emu_hwid))
        full_devices = []
        for port in ports:
            if app:
                if app.fabricator_list.getFabricatorByPort(port) is None:
                    print(f"Creating device for port: {port}")
                    if port.comm_port == emu_port:
                        values = app.emulator_connections.values()
                        ws = next(iter(values), None)
                        device = Fabricator.staticCreateDevice(port, websocket_connection=ws)
                    else:
                        print("not an emu")
                        device = Fabricator.staticCreateDevice(port)
                    print(f"created device: {device}")
                    full_devices.append(device)
            else:
                full_devices.append(Fabricator(port.comm_port).device)
        print(f"Full devices: {full_devices}")
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
        :rtype: list[str]
        """
        return app.resource_manager.list_resources()

    @staticmethod
    def getPortByName(name: str):
        """
        Get a specific port by its device name.
        :param name: The name of the device.
        :type name: str
        :return: The port object
        :rtype: str | None
        """
        assert isinstance(name, str), f"Name must be a string: {name} : {type(name)}"
        ports = Ports.getListPorts()
        if len(app.emulator_connections) > 0:
            emu_port, emu_name, emu_hwid = app.get_emu_ports()
            if emu_port and emu_name and emu_hwid and emu_port == name:
                return EmuTCPIPInstrument(app.resource_manager, emu_port, description="Emulator", hwid=emu_hwid)
        for port in ports:
            if not port: continue
            if re.match(r'ASRL\d+::INSTR', port):
                port = re.sub(r'ASRL', system_device_prefix, re.sub(r'::INSTR', '', port))
            if port in name:
                return port
        return None

    @staticmethod
    def getPortByHwid(hwid: str):
        """
        Get a specific port by its hardware ID.
        :param str hwid: The hardware ID of the device.
        :rtype: ListPortInfo | SysFS | None
        """
        # TODO: make this return the pyvisa version of the port. not critical
        assert isinstance(hwid, str), f"HWID must be a string: {hwid} : {type(hwid)}"
        ports = serial.tools.list_ports.comports()
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
    def diagnosePort(port: Resource) -> str:
        """
        Diagnose a port to check if it is functional by sending basic G-code commands.
        :param Resource port: The port to diagnose
        :rtype: str
        """
        try:
            if app:
                device = app.fabricator_list.getFabricatorByPort(port).device
            else:
                device = Fabricator(port.resource_name).device
            if not device:
                return "Device creation failed."

            device.connect()
            sendGcode("M115")
            response = device.getSerialConnection().read().strip()
            device.disconnect()

            return f"Diagnosis result for {port.resource_name}: {response}"
        except Exception as e:
            return f"Error diagnosing port {port.resource_name}: {e}"