import { GenericMarlinFabricator } from "./generic.js";

/** @todo Possibly incomplete */
export class Prusai3MK3 extends GenericMarlinFabricator {
    RESPONSE_TIMEOUT = 10000;
    BOOT_TIME = 5000;
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+/;
}