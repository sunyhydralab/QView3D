/** 
 * @todo BIG TODO: Add ANSI colors to logged outputs to make them easier to read, 
 * create a module that will host all of the debug functions, including this function 
 */
export var DEBUG_ENABLED = true; 

import { GenericSerialFabricator } from './serial_fabricator.js';

// TEMP
class PrusaMK3 extends GenericSerialFabricator {
    RESPONSE_TIMEOUT = 10000;
    BOOT_TIME = 5000;
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+/;
}

/** @todo Add a helper function that determines which specific class to use */
const fab1 = new PrusaMK3('/dev/ttyACM1');
const fab2 = new GenericSerialFabricator('/dev/ttyACM0');

// Test sending G-Code
import * as fs from 'node:fs';

let gcode_file_split = fs.readFileSync('./xyz-cali-cube-micro_MK3.gcode', { encoding: "utf8" }).split('\n');

// Remove empty lines and lines that start with ';'
let filtered_gcode_file = gcode_file_split.filter(line => line.trim() !== '' && !line.trim().startsWith(';'));

for await (let gcode_line of filtered_gcode_file) {
    gcode_line = gcode_line.split(';')[0];

    fab1.addGCodeInstructionToQueue({ instruction: gcode_line + '\n' });
}

gcode_file_split = fs.readFileSync('./xyz-cali-cube-mini_MK4.gcode', { encoding: "utf8" }).split('\n');

// Remove empty lines and lines that start with ';'
filtered_gcode_file = gcode_file_split.filter(line => line.trim() !== '' && !line.trim().startsWith(';'));

for await (let gcode_line of filtered_gcode_file) {
    gcode_line = gcode_line.split(';')[0];

    fab2.addGCodeInstructionToQueue({ instruction: gcode_line + '\n' });
} 