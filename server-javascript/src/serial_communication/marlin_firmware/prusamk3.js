import { GenericSerialFabricator } from "./generic_serial_fabricator.js";

/** @todo Possibly incomplete */
export class Prusai3MK3 extends GenericSerialFabricator {
    RESPONSE_TIMEOUT = 10000;
    BOOT_TIME = 5000;
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+/;
}