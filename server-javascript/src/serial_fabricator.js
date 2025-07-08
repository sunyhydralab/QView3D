'use strict';

// Used to communicate with serial devices
import { SerialPort } from 'serialport';

/**
 * The anotomy of response extractor type
 * @typedef {Object} ResponseExtractor
 * @property {RegExp} regex A regular expression used to extract specific values from a fabricator's response
 * @property {(extractorResult: any) => void} [callback] A function called when the extractor gets a result
 */

/**
 * The anotomy of G-Code instruction type
 * @typedef {Object} GCodeInstruction
 * @property {string} instruction The G-Code instruction to send to the fabricator
 * @property {ResponseExtractor} [extractor] The extractor used to get the response from the fabricator
 */

/**
 * The anotomy of FirmwareInfo type
 * @typedef {Object} FirmwareInfo
 * @property {string} [firmwareVersion]
 * @property {string} [machineType]
 * @property {string} [UUID]
 */

/**
 * A generic class used to communicate with G-Code enabled fabricators over serial. This class is meant to be **extended**
 * 
 * It assumes that the fabricator is flashed with {@link https://github.com/MarlinFirmware/Marlin Marlin firmware}
 * @class
 */
class GenericSerialFabricator {
    /** 
     * Baud rate of the connection to the serial port
     * @readonly 
     * @type {number} 
     */
    BAUD_RATE = 115200;

    /**
     * The amount of time to wait in ms before sending G-Code commands to the fabricator
     * @readonly 
     * @type {number} 
     */
    BOOT_TIME = 800;

    /** 
     * The maximum amount of time to wait for a response from a fabricator in ms
     * @readonly
     * @type {number}
     */
    RESPONSE_TIMEOUT = 10000;

    /** 
     * The character encoding used to transmit and receive messages
     * @readonly 
     * @type {BufferEncoding} 
     */
    CHARACTER_ENCODING = 'utf8';

    /** 
     * The string to use to split the response received by the fabricator
     * @readonly
     * @type {string}
     */
    LINE_SPLITTER = '\n';

    /** 
     * The string to expect when G-Code is fully processed by a fabricator
     * @readonly
     * @type {string}
     */
    GCODE_PROCESSED_RESPONSE = 'ok\n';

    /** 
     * String buffer used internally to process results from G-Code command instructions
     * @type {string}
     */
    #responseBuf = '';

    /** 
     * A queue containing all of the G-Code instructions to be sent to a fabricator
     * @type {GCodeInstruction[]}
     */
    #instructQ = [];

    /** 
     * A queue containing all of the regexes that will be used to extract information from the fabricator's reponse
     * @type {ResponseExtractor[]}
     */
    #extractQ = [];

    /** 
     * Used to determine if the fabricator can be booted from
     * @type {boolean}
     */
    #hasBooted = false;

    /** 
     * Used to communicate with a serial port
     * @readonly
     * @type {SerialPort}
     */
    #openPort;

    /**
     * This value is cached to prevent the RegExp constructor from being called so many times
     * @todo This is gross. Cleanup
     * @readonly
     * @type {RegExp}
     */
    #gcodeProcessedResponseRegex = new RegExp(`(${this.GCODE_PROCESSED_RESPONSE.split(this.LINE_SPLITTER)[0]})`);

    /**
     * @param {string} port The name of the port e.g., `/dev/ttyACM0` on Linux systems or `COM1` on Windows
     */
    constructor(port) {
        this.#openPort = new SerialPort({ path: port, baudRate: this.BAUD_RATE });

        // Wait a specific amount of time before allowing G-Code commands to be sent over serial
        setTimeout(() => this.#hasBooted = true, this.BOOT_TIME);

        // When data is received, this callback function will run
        this.#openPort.on('data', chunk => {
            if (chunk instanceof Buffer)
                chunk = chunk.toString(this.CHARACTER_ENCODING);

            if (typeof chunk === 'string')
                this.#responseBuf += chunk;
            else
                throw new Error(`Stream ${this} is in object mode which is currently not supported by the default data processor in the GenericSerialFabricator class.`);

            
            /** @todo Probably don't split by LINE_SPLITTER but instead split by GCODE_PROCESSED_RESPONSE. **NOTE** Check with @see gcodeProcessedResponseRegex before making edits */
            // Split each line by the line splitter value
            const lines = this.#responseBuf.split(this.LINE_SPLITTER);

            if (this.#extractQ.length > 0) {
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    
                    /** @type {ResponseExtractor[]} Extractors that aren't used yet */
                    let unusedExtractors = [];

                    while (this.#extractQ.length !== 0) {
                        const extractor = this.#extractQ.shift();
                        
                        if (extractor !== undefined) { /** @todo ts-server thinks this value can be undefined, but we know it can't be because there are elements in the array. Try fix? */
                            const extractorResult = extractor.regex.exec(line);

                            // If we get a result, then this extractor has found what it wanted
                            if (extractorResult !== null) {
                                if (extractorResult.groups === undefined) {
                                    /** @todo Make this log have a warning mode where it will do console.warn instead of console.info */
                                    if (DEBUG_ENABLED)
                                        console.info(`The extractor ${extractor.regex} did not provide named capture groups in its implementation. But it still found a match`);
                                }

                                if (extractor.callback !== undefined) {
                                    // The result is stored as an object in the capture group
                                    extractor.callback(extractorResult.groups);

                                    if (DEBUG_ENABLED) {
                                        if (extractorResult.groups === undefined) 
                                            console.info(`The extractor ${extractor.regex} returned undefined from ${line}`);
                                        else
                                            console.info(`The extractor ${extractor.regex} returned ${Object.values(extractorResult.groups)}} from ${line}`);
                                    }

                                    break; /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                                } else {
                                    throw new Error(`The extractor ${extractor.regex} has no callback function. It extracted the results ${extractorResult.groups}`);
                                }
                            } else {
                                // Else, the extractor has not got what it wanted and should be re-added to the queue
                                unusedExtractors.push(extractor);

                                if (DEBUG_ENABLED) /** @todo Add a DEBUG_ENABLED global object with multiple flags that will enable/disable the logging of different events */
                                    console.info(`The extractor ${extractor.regex} failed to match ${line}`);
                            }
                        }
                    }

                    // Update the extractor queue
                    this.#extractQ = unusedExtractors;
                }
            }

            if (this.#responseBuf.includes(this.GCODE_PROCESSED_RESPONSE)) {
                if (this.#instructQ.length > 0) {
                    const nextInstr = this.#instructQ.shift();

                    if (nextInstr !== undefined) { /** @todo ts-server thinks this value can be undefined, but we know it can't be because there are elements in the array. Try fix? */
                        this.#openPort.write(nextInstr.instruction, this.CHARACTER_ENCODING);
                        
                        if (nextInstr.extractor !== undefined)
                            this.#extractQ.push(nextInstr.extractor);
                        else
                            throw new Error(`All instructions must have an extractor so that they resolve their operation. Instruction ${nextInstr.instruction} given to fabricator at port ${this.#openPort.path} has no extractor`);
                    }
                }
            }

            // Because the last line could be incomplete, add that line to the buffer. All other lines are discarded as noise
            this.#responseBuf = lines[lines.length - 1];
        })
    }

    /**
     * Sends a G-Code instruction to a fabricator, and uses the extractor to return the result
     * If no response is received after RESPONSE_TIMEOUT, this promise will reject with an error
     * @param {GCodeInstruction} gcodeInstruction The G-Code instruction to send to the fabricator
     * @returns {Promise<any>}
     */
    sendGCodeInstruction(gcodeInstruction) {
        /**
         * Internal function used to not write code twice
         * @param {(value: any) => void} resolve 
         * @param {([reason]: any) => void} reject 
         */
        const _sendGCode = (resolve, reject) => {
            let extractor = gcodeInstruction.extractor;

            if (extractor === undefined) {
                gcodeInstruction.extractor = { regex: this.#gcodeProcessedResponseRegex }

                extractor = gcodeInstruction.extractor /** @todo Is this really necessary? (It fixes a type error) */
                if (DEBUG_ENABLED)
                    console.info(`Instruction ${gcodeInstruction.instruction.trim()} was automatically given an extractor`);
            }
            
            if (extractor.callback === undefined) {
                // Set the extractor method to the resolver
                extractor.callback = resolve;
                
                // If nothing is in the instruction queue, then we'll send a dummy instruction to start the communication loop
                if (this.#instructQ.length === 0)
                    this.#openPort.write(this.DUMMY_INSTRUCTION);
            
                this.#instructQ.push(gcodeInstruction);
            } else {
                throw new Error(`The sendGCode function in the GenericSerialFabricator class does not support custom callback functions in extractors. The instruction ${gcodeInstruction} has a custom callback function`);
            }

        return new Promise((resolve, reject) => {
            // The command times out after the timeout amount
            setTimeout(() => {
                reject(
                    new Error(`The instruction ${gcodeInstruction.instruction.trim()} with extractor ${gcodeInstruction.extractor?.regex} timed out for fabricator on port ${this.#openPort.path}`)
                );
            }, this.RESPONSE_TIMEOUT);
        }

        return new Promise((resolve, reject) => {
            // If it hasn't booted up yet, then wait the boot time
            if (this.#hasBooted === false)
                setTimeout(_sendGCode, this.BOOT_TIME, resolve, reject);
            else
                _sendGCode(resolve, reject);
        });
    }

    // Commands to communicate with fabricators
	// ..._CMD is the command, 
    // ..._CMD_EXTRACTOR is used to get the output of the command
    /** @readonly @type {string} */
    INFO_CMD = 'M115\n';

    /** @readonly @type {RegExp} */
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+UUID:(?<UUID>[^\s]+)/;

    /**
     * @returns {Promise<FirmwareInfo>}
     */
    async getFirmwareInfo() {
        /** @type {ResponseExtractor} */
        const extractor = {
            regex: this.INFO_CMD_EXTRACTOR,
            callback: undefined
        }

        /** @type {GCodeInstruction} */
        const instruction = {
            instruction: this.INFO_CMD,
            extractor: extractor
        }
        
        return await this.sendGCode(instruction);
    }
}

var DEBUG_ENABLED = true; /** @todo BIG TODO: Add ANSI colors to logged outputs to make them easier to read, create a module that will host all of the debug functions, including this function */

class PrusaMK3 extends GenericSerialFabricator {
    RESPONSE_TIMEOUT = 10000;
    BOOT_TIME = 5000;
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+/;
}

class TestFab extends GenericSerialFabricator {
    RESPONSE_TIMEOUT = 10000000;
}

const testFabricator = new TestFab('/dev/pts/2');

console.log(await testFabricator.getFirmwareInfo());

console.log(await testFabricator.sendGCode({ instruction: 'M69\n'}));