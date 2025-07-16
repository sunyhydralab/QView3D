'use strict';

// Used to communicate with serial devices
import { SerialPort } from 'serialport';
import { DEBUG_FLAGS } from '../../flags.js';

/**
 * @typedef FabricatorResponse
 * @property {'processed' | 'unsupported' | 'fabricator-disconnected' | 'timed-out' | 'unexpected-response'} status The status of the fabricator response
 * @property {Object.<string, string>} [extractedResults] The data returned by the response extractor
 */

/**
 * @typedef ResponseExtractor
 * @property {RegExp} [regex] A regular expression used to extract specific values from a fabricator's response
 * @property {function(FabricatorResponse): void} callback A function called when the extractor gets a result
 */

/**
 * @typedef InstructionExtractor
 * @property {string} instruction The G-Code instruction to send to the fabricator
 * @property {ResponseExtractor} extractor The extractor used to get the response from the fabricator
 */

/**
 * A generic class used to communicate with G-Code enabled fabricators over serial. This class is meant to be **extended**
 * 
 * It assumes that the fabricator is flashed with {@link https://github.com/MarlinFirmware/Marlin Marlin firmware}
 */
export class GenericSerialFabricator {
    /** 
     * Baud rate of the connection to the serial port
     * @readonly 
     * @type {number} 
     */
    BAUD_RATE = 115200;

    /**
     * The amount of time to wait in ms before sending G-Code instructions to the fabricator
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
     * The dummy instruction to send to the fabricator when there's nothing in the instruction queue
     * @readonly
     * @type {string}
     */
    DUMMY_INSTRUCTION = 'M118 Hello, human.\n';

    /**
     * The dummy instruction's extractor regex
     * @readonly
     * @type {RegExp}
     */
    DUMMY_INSTRUCTION_EXTRACTOR_REGEX = /(?<dumbo>Hello, human.)/;

    /** 
     * String buffer used internally to process results from G-Code instructions
     * @type {string}
     */
    #responseBuf = '';

    /** 
     * A queue containing all of the G-Code instructions to send to a fabricator
     * @type {InstructionExtractor[]}
     */
    #instructQ = [];

    /** 
     * A queue containing all of the regexes that will be used to extract information from a fabricator's reponse
     * @type {ResponseExtractor[]}
     */
    #extractQ = [];

    /** 
     * Used to determine if the fabricator is ready to receive G-Code instructions
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
     * Debounce used to prevent dummy instructions from being sent multiple times at once
     * @type {boolean}
     */
    #dummyInstructionBeingSent = false;

    /**
     * @param {string} port The name of the port e.g., `/dev/ttyACM0` on Linux systems or `COM1` on Windows
     */
    constructor(port) {
        this.#openPort = new SerialPort({ path: port, baudRate: this.BAUD_RATE });

        // Wait a specific amount of time before allowing G-Code instructions to be sent over serial
        setTimeout(() => this.#hasBooted = true, this.BOOT_TIME);

        // When data is received, this callback function will run
        this.#openPort.on('data', chunk => {
            if (chunk instanceof Buffer)
                chunk = chunk.toString(this.CHARACTER_ENCODING);

            if (typeof chunk === 'string')
                this.#responseBuf += chunk;
            else
                throw new Error(`Stream at port ${this.#openPort.path} is in object mode which is currently not supported by the default data processor in the GenericSerialFabricator class.`);

            /** @todo Probably don't split by LINE_SPLITTER but instead split by GCODE_PROCESSED_RESPONSE */
            // Split each line by the line splitter value
            const lines = this.#responseBuf.split(this.LINE_SPLITTER);

            if (this.#extractQ.length > 0) {
                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];

                    const extractorCount = this.#extractQ.length;
                    let extractorsRan = 0;

                    while (extractorCount > extractorsRan) {
                        extractorsRan++;
                        /** @type {ResponseExtractor} */
                        // @ts-ignore It's impossible for this to be undefined since there has to be something in the array
                        const extractor = this.#extractQ.shift();

                        if (extractor.regex !== undefined) {
                            const extractorResult = extractor.regex.exec(line);

                            // If we get a result, then this extractor has found what it wanted
                            if (extractorResult !== null) {
                                if (extractorResult.groups === undefined)
                                    throw new Error(`The extractor ${extractor.regex} did not provide named capture groups in its implementation. This behavior is not supported in the GenericSerialFabricator class`);

                                // The result is stored as an object in the capture group
                                extractor.callback({ status: 'processed', extractedResults: extractorResult.groups });

                                if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.SHOW_EXTRACTOR_RESULT)
                                    console.info(`The extractor ${extractor.regex} returned ${Object.values(extractorResult.groups)} from ${line}`);

                                break; /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                            } else {
                                // Else, the extractor has not got what it wanted and should be re-added to the queue
                                this.#extractQ.push(extractor);

                                if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.EXTRACTOR_FAILED_MATCH)
                                    console.info(`The extractor ${extractor.regex} failed to match ${line}`);
                            }
                        } else {
                            if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.MISSING_REGEX)
                                console.info(`The extractor with the callback function ${extractor.callback} has no regex and therefore won't extract anything`);

                            // If no regex is present, then it is assumed that this extractor wants to see 
                            // if the this.GCODE_PROCESSED_RESPONSE is present in the fabricator's response
                            if (this.#responseBuf.includes(this.GCODE_PROCESSED_RESPONSE)) {
                                extractor.callback({ status: 'processed' });

                                break;  /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                            }
                        }
                    }
                }
            }

            if (this.#responseBuf.includes(this.GCODE_PROCESSED_RESPONSE)) {
                if (this.#instructQ.length > 0) {
                    /** @type {InstructionExtractor} */
                    // @ts-ignore It's impossible for this to be undefined since there has to be something in the array
                    const nextInstr = this.#instructQ.shift();

                    this.#openPort.write(nextInstr.instruction, this.CHARACTER_ENCODING);
                    this.#extractQ.push(nextInstr.extractor);
                }
            }

            // Because the last line could be incomplete, add that line to the buffer. All other lines are discarded as noise
            this.#responseBuf = lines[lines.length - 1];
        })
    }

    /**
     * Sends a G-Code instruction to a fabricator, and uses the extractor to return the result
     * If no response is received after this.RESPONSE_TIMEOUT, this promise will reject with an error
     * @param {string} instruction The G-Code instruction to send to the fabricator
     * @param {RegExp} [extractorRegEx] The extractor to be used with this G-Code instruction
     * @param {boolean} [writeNow = false] Whether or not the G-Code instruction will be added to the queue or immediately sent to the fabricator (**Warning unsafe**)
     * @returns {Promise<FabricatorResponse>}
     */
    sendGCodeInstruction(instruction, extractorRegEx, writeNow = false) {
        /**
         * Internal function used to not write code twice
         * @param {function(any): void} resolve
         * @param {function(any=): void} reject
         */
        const _sendGCode = (resolve, reject) => {
            if (writeNow === false) {
                if (this.#extractQ.length === 0) {
                    // Add the extractor to the extract queue since it won't be automatically added
                    this.#extractQ.push({ regex: extractorRegEx, callback: resolve });

                    // Immediately write to the port
                    this.#openPort.write(instruction, this.CHARACTER_ENCODING);
                } else {
                    this.#instructQ.push({
                        instruction: instruction,
                        extractor: {
                            regex: extractorRegEx,
                            callback: resolve
                        }
                    });
                }

                if (this.#instructQ.length > 50)
                    if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.MANY_GCODE_INSTRUCTIONS)
                        console.warn(`Fabricator at port ${this.#openPort.path} has over 50 G-Code instructions in its queue which is abnormal. The sendGCodeInstruction returns a promise that should be awaited.`);

            } else if (writeNow === true) {
                // Add the extractor to the extract queue since it won't be automatically added
                this.#extractQ.push({ regex: extractorRegEx, callback: resolve });

                // Immediately write to the port
                this.#openPort.write(instruction, this.CHARACTER_ENCODING);

                if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.SHOW_POTENTIALLY_UNSAFE_WRITES)
                    console.warn(`The G-Code instruction ${instruction.trim()} was immediately written to port ${this.#openPort.path}. This will likely lead to abnormal behavior`);
            }

            // The request times out after the timeout amount
            setTimeout(() => {
                reject(
                    new Error(`The instruction ${instruction.trim()} with extractor ${extractorRegEx} timed out for fabricator on port ${this.#openPort.path}`)
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

    /**
     * Sends a dummy instruction to the fabricator. Uses this.DUMMY_INSTRUCTION
     * This is typically used to start the processing loop between Qview3D and the fabricator
     * @param {boolean} [writeNow = true] If this dummy instruction should be added to the instruction queue or sent directly to the fabricator
     * @returns {Promise<FabricatorResponse>}
     */
    async sendDummyInstruction(writeNow = true) {
        if (this.#dummyInstructionBeingSent === false) {
            this.#dummyInstructionBeingSent = true;
            /** @type {FabricatorResponse} */
            let response;

            try {
                response = await this.sendGCodeInstruction(this.DUMMY_INSTRUCTION, this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX, writeNow);
            } catch (e) {
                // Show the timeout error, but don't crash the program
                console.warn(e);
                response = { status: 'timed-out' };
            }

            this.#dummyInstructionBeingSent = false;

            if (response.status === 'processed')
                return response;
            else if (response.status === 'timed-out')
                return response;

            if (DEBUG_FLAGS.SHOW_EVERYTHING || DEBUG_FLAGS.UNHANDLED_STATES) {
                console.warn(`The sendDummyInstruction function has experienced an unhandled state! The status from the fabricator was ${response.status} instead of processed or timed-out`);
                // Some useful info
                console.warn(`Fabricator at port: ${this.#openPort.path}\nG-Code instruction sent: ${this.DUMMY_INSTRUCTION}\nExtractor used: ${this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX}`);
            }

            return { status: 'unexpected-response' };
        } else {
            throw new Error(`A dummy instruction was already sent to fabricator at port ${this.#openPort.path}. Was this intentional?`);
        }
    }

    /** @todo command -> instruction for consistency */
    // Commands to communicate with fabricators
    // ..._CMD is the command, 
    // ..._CMD_EXTRACTOR is used to get the output of the command
    /** 
     * @readonly 
     * @type {string}
     */
    INFO_CMD = 'M115\n';

    /** 
     * @readonly 
     * @type {RegExp} 
     */
    INFO_CMD_EXTRACTOR = /FIRMWARE_NAME:(?<firmwareVersion>[^\s]+).+MACHINE_TYPE:(?<machineType>[^\s]+).+UUID:(?<UUID>[^\s]+)/;

    /**
     * Returns the firmware information for the given fabricator
     * @returns {Promise<FabricatorResponse>}
     */
    getFirmwareInfo() {
        return this.sendGCodeInstruction(this.INFO_CMD, this.INFO_CMD_EXTRACTOR);
    }
}