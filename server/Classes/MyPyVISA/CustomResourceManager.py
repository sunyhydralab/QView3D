import re
from pyvisa import ResourceManager, constants
from Classes.MyPyVISA.CustomSerialInstrument import CustomSerialInstrument
from Classes.MyPyVISA.CustomTCPIPInstrument import CustomTCPIPInstrument
from globals import system_device_prefix
class CustomResourceManager(ResourceManager):
    ResourceManager._resource_classes[constants.InterfaceType.asrl, "INSTR"] = CustomSerialInstrument
    ResourceManager._resource_classes[constants.InterfaceType.tcpip, "INSTR"] = CustomTCPIPInstrument
    ResourceManager._resource_classes[constants.InterfaceType.tcpip, "SOCKET"] = CustomTCPIPInstrument

    def open_resource(self, resource_name, **kwargs):
        """Ensure serial instruments are instantiated using CustomSerialInstrument."""
        if resource_name and re.match(r"COM\d+", resource_name):
            resource_name = f"{re.sub("COM", 'ASRL', resource_name)}::INSTR"
        open_resources = self.list_opened_resources()
        if open_resources:
            resource = next((res for res in open_resources if res.resource_name == resource_name), None)
            if resource: return resource
        if re.match(r"ASRL\d+::INSTR", resource_name):
            printer = CustomSerialInstrument(self, resource_name, **kwargs)
            self._created_resources.add(printer)
            return printer
        elif re.match(r"TCPIP", resource_name):
            printer = CustomTCPIPInstrument(self, resource_name, **kwargs)
            self._created_resources.add(printer)
            return printer

        return super().open_resource(resource_name, **kwargs)
