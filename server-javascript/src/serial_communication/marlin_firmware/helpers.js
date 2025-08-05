// Import relevant debug flags
import { ENABLE_ALL_FLAGS, UNHANDLED_STATES } from "../../flags.js";
import { GenericMarlinFabricator } from "./generic.js";

/**
 * Finds the correct class to be used to communicate with a fabricator at a serial port
 * @param {string} port The name of the port e.g., `/dev/ttyACM0` on Linux systems or `COM1` on Windows
 * @returns {Promise<GenericMarlinFabricator>} 
 */
export async function getFabricatorFromSerialPort(port) {
    // GenericMarlinFabricator is the class used to receive information from fabricators by default
    let fab = new GenericMarlinFabricator(port);

    let timeouts = 0;
    let isResponding = false;

    while (isResponding === false) {
        // Use a dummy instruction to wake up the fabricator and then wait for it to respond
        const response = await fab.sendDummyInstruction();

        if (response.status === 'processed')
            isResponding = true;
        else if (response.status === 'timed-out')
            timeouts++;

        // If we timeout too much, then we're probably 'breaking' the fabricator by sending data to it when it's not ready
        // Therefore, we have to use a fabricator with a greater BOOT_TIME
        if (timeouts > 3) {
            // Wait for the connection to close for the current fabricator
            await fab.closeSerialConnection();

            // Increase the boot time by 1 second
            fab = new GenericMarlinFabricator(port, {BOOT_TIME: fab.BOOT_TIME + 1000});
        }
    }

    
    
    return fab;
}