'use strict';

// Used to communicate with serial devices
import { SerialPort } from 'serialport';
import { DEBUG_FLAGS as DF } from '../../flags.js';

/**
 * @todo Turn below into simple classes so we can have runtime checks (or not?)
 */

/**
 * @typedef FabricatorResponse
 * @property {'processed' | 'unsupported' | 'fabricator-disconnected'} status The status of the fabricator response
 * @property {Object.<string, string>} [extractedResults] The data returned by the response extractor
 */

/**
 * @typedef ResponseExtractor
 * @property {RegExp} regex A regular expression used to extract specific values from a fabricator's response
 * @property {function(FabricatorResponse): void} callback A function called when the extractor gets a result
 */

/**
 * @typedef InstructionExtractor
 * @property {string} instruction The G-Code instruction to send to the fabricator
 * @property {ResponseExtractor} extractor The extractor used to get the response from the fabricator
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
 */
export class GenericSerialFabricator {
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
                    
                    /** 
                     * Extractors that aren't used yet
                     * @type {ResponseExtractor[]} 
                     */
                    let unusedExtractors = [];

                    while (this.#extractQ.length !== 0) {
                        const extractor = this.#extractQ.shift();
                        
                        if (extractor !== undefined) { /** @todo ts-server thinks this value can be undefined, but we know it can't be because there are elements in the array. Try fix? */
                            const extractorResult = extractor.regex.exec(line);

                            // If we get a result, then this extractor has found what it wanted
                            if (extractorResult !== null) {
                                if (extractorResult.groups === undefined)
                                    throw new Error(`The extractor ${extractor.regex} did not provide named capture groups in its implementation. This behavior is not supported in the GenericSerialFabricator class`);

                                if (extractor.callback === undefined)
                                    throw new Error(`The extractor ${extractor.regex} has no callback function which isn't supported. It extracted the results ${extractorResult.groups}`);

                                // The result is stored as an object in the capture group
                                extractor.callback(extractorResult.groups);

                                if (DF.SHOW_EVERYTHING || DF.SHOW_EXTRACTOR_RESULT)
                                        console.info(`The extractor ${extractor.regex} returned ${Object.values(extractorResult.groups)} from ${line}`);

                                break; /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                            } else {
                                // Else, the extractor has not got what it wanted and should be re-added to the queue
                                unusedExtractors.push(extractor);

                                if (DF.SHOW_EVERYTHING || DF.EXTRACTOR_FAILED_MATCH)
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
                        
                        if (nextInstr.extractor !== undefined) {
                            this.#extractQ.push(nextInstr.extractor);
                        } else {
                            if (DF.SHOW_EVERYTHING || DF.NO_EXTRACTOR_PRESENT)
                                console.info(`G-Code instruction ${nextInstr.instruction.trim()} for fabricator at port ${this.#openPort.path} has no extractor so no result will be returned`);
                        }
                    }
                }
            }

            // Because the last line could be incomplete, add that line to the buffer. All other lines are discarded as noise
            this.#responseBuf = lines[lines.length - 1];
        })
    }

    /**
     * Sends a dummy instruction to the fabricator. Uses this.DUMMY_INSTRUCTION
     * This is typically used to start the processing loop between Qview3D and the fabricator
     */
    sendDummyInstruction() {
        const _sendDummyInstruction = () => {
            // Used to indicate to the timeout function that the current operation completed successfully
            let operationCompleted = false;

            /** @type {ResponseExtractor} */
            const extractor = {
                regex: this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX,
                callback: (response) => {
                    operationCompleted = true;
                    this.#dummyInstructionBeingSent = false;

                    if (DF.SHOW_EVERYTHING || DF.SHOW_DUMMY_EXTRACTOR_RESPONSE)
                        console.info(`The dummy instruction at port ${this.#openPort.path} returned the result ${Object.values(response)}`);
                }
            }

            // The extractor is used to determine if the fabricator has sent back the expected response
            this.#extractQ.push(extractor);

            this.#openPort.write(this.DUMMY_INSTRUCTION, this.CHARACTER_ENCODING);

            /**
             * @todo Maybe consider not making this error? (Dummy instructions can be used to determine if the fabricator is behaving normally)
             */
            setTimeout(() => {
                if (operationCompleted === false)
                    throw new Error(`The dummy instruction ${this.DUMMY_INSTRUCTION.trim()} with extractor ${this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX} timed out for fabricator on port ${this.#openPort.path}`); 
            }, this.RESPONSE_TIMEOUT);
        }

        // Ensure a dummy instruction isn't currently being sent to the fabricator
        if (this.#dummyInstructionBeingSent === false) {
            this.#dummyInstructionBeingSent = true;

            if (this.#hasBooted === true)
                _sendDummyInstruction();
            else
                setTimeout(_sendDummyInstruction, this.BOOT_TIME);
        } else {
            if (DF.SHOW_EVERYTHING || DF.EXTRA_DUMMY_INSTRUCTION)
                console.info(`A dummy instruction was already sent to fabricator at port ${this.#openPort.path}. Was this intentional?`);
        }
    }

    /**
     * Adds a G-Code instruction to a fabricator's instruction queue. **The processing loop is not automatically started**
     * No timeout error is thrown, nor is a response returned
     * @param {string} instruction The G-Code instruction to send to the fabricator
     * @param {ResponseExtractor} [customExtractor] A custom extractor that can be used to handle the results from a G-Code instruction
     * @returns {undefined}
     */
    addGCodeInstructionToQueue(instruction, customExtractor) {
        /** FUTURE @todo Add a parser that ensures that the instruction sent is supported (correct syntax and supported by this implementation) */
        if (customExtractor !== undefined)
            if (customExtractor.callback === undefined)
                throw new Error(`The G-Code instruction ${instruction.trim()} has the extractor ${customExtractor.regex} but has no callback function. This is unsupported in the GenericSerialFabricator class`);

        this.#instructQ.push({ instruction: instruction, extractor: customExtractor });
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
     * @returns {Promise<FirmwareInfo>}
     */
    async getFirmwareInfo() {
        /** @type {ResponseExtractor} */
        const extractor = {
            regex: this.INFO_CMD_EXTRACTOR,
            callback: undefined
        }
        
        return await this.sendGCodeInstruction(this.INFO_CMD, extractor);
    }
}