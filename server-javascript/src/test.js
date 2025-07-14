import { GenericSerialFabricator } from './serial_communication/marlin_firmware/generic_serial_fabricator.js';
import { Prusai3MK3 } from './serial_communication/marlin_firmware/prusamk3.js';

/** @todo Add a helper function that determines which specific class to use */
const fab1 = new Prusai3MK3('/dev/ttyACM1');
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

// Starts the processing loop
fab2.sendDummyInstruction();