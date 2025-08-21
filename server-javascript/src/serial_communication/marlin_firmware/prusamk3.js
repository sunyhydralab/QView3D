import { GenericMarlinFabricator } from "./generic.js";

/** @todo Possibly incomplete */
export class Prusai3MK3 extends GenericMarlinFabricator {
    static SUPPORTED_FABRICATORS = ['Prusa i3 MK3S'];
    RESPONSE_TIMEOUT = 10000;
    BOOT_TIME = 5000;
}