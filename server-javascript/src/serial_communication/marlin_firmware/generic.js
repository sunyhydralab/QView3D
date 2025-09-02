'use strict';

// Used to communicate with serial devices
import { SerialPort } from 'serialport';
// Import relevant debug flags
import { 
    ENABLE_ALL_FLAGS, EXTRACTOR_FAILED_MATCH, FABRICATOR_CONNECTION_CLOSED, 
    FABRICATOR_IDLE, MANY_GCODE_INSTRUCTIONS, MISSING_REGEX, 
    SHOW_EXTRACTOR_RESULT, SHOW_EXTRACTOR_STATE_AFTER_TIMEOUT, 
    SHOW_POTENTIALLY_UNSAFE_WRITES, SHOW_TIMED_OUT_INSTRUCTIONS, 
    UNHANDLED_STATES, FABRICATOR_CONNECTION_OPENED
} from '../../flags.js';

/**
 * @typedef FabricatorResponse
 * @property {'processed' | 'unsupported' | 'fabricator-disconnected' | 'timed-out' | 'unexpected-response'} status The status of the fabricator response
 * @property {Object} [extractedResults] The data returned by the response extractor
 */

/**
 * @typedef ResponseExtractor
 * @property {RegExp[]} [regexes] A regular expression used to extract specific values from a fabricator's response
 * @property {'in-progress' | 'done' | 'started' | 'stale' | 'timed-out' | 'will-never-complete'} status Status of the fabricator's response
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
export class GenericMarlinFabricator {
    /**
     * Used to figure out which fabricator should use this class
     * @readonly
     * @static
     * @type {string[]}
     */
    static SUPPORTED_FABRICATORS = ['all'];

    /** 
     * Baud rate of the connection to the serial port
     * @readonly 
     * @type {number} 
     */
    BAUD_RATE = 115200;

    /**
     * Used to determine what counts as an abnormal amount of requests to a fabricator at once
     * This is mostly used for debugging purposes
     * @readonly
     * @type {number}
     */
    ABNORMAL_REQUEST_AMOUNT = 4;

    /**
     * The amount of time to wait in ms before sending G-Code instructions to the fabricator
     * @readonly 
     * @type {number} 
     */
    BOOT_TIME = 800;

    /**
     * The amount of time before the fabricator becomes idle (and therefore we need to wait for it to boot up again before sending another instruction)
     * @readonly
     * @type {number}
     */
    IDLE_TIMEOUT = 120000;

    /** 
     * The maximum amount of time to wait for a response from a fabricator in ms
     * @readonly
     * @type {number}
     */
    RESPONSE_TIMEOUT = 7000;

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
     * @param {Object} [overrides] Used to dynamically override any of the default properties of this class **unsafe**
     */
    constructor(port, overrides) {
        Object.assign(this, overrides); /** @todo Add something that checks to see if the properties provided are valid? */

        this.#openPort = new SerialPort({ path: port, baudRate: this.BAUD_RATE });

        if (ENABLE_ALL_FLAGS || FABRICATOR_CONNECTION_OPENED)
            console.info(`A connection has been opened at port '${port}' with baud rate '${this.BAUD_RATE}'`);

        // Wait a specific amount of time before allowing G-Code instructions to be sent over serial
        const hasBootedTimeout = setTimeout(() => this.#hasBooted = true, this.BOOT_TIME);

        // Internal function used to determine whether or not the current fabricator is idle
        const _handleIdle = () => {
            this.#hasBooted = false;
            // Refreshes the boot up timer because we have to wait for the fabricator to boot up again
            hasBootedTimeout.refresh();

            if (ENABLE_ALL_FLAGS || FABRICATOR_IDLE)
                console.info(`The fabricator at port ${this.#openPort.path} is idle`);
        }

        // Automatically make the fabricator idle after the this.IDLE_TIMEOUT has passed
        const handleIdleTimeout = setTimeout(_handleIdle, this.IDLE_TIMEOUT);

        /**
         * When data is received, this callback function will run
         * @param {Buffer | string | any} chunk
         */
        const dataListener = (chunk) => {
            if (chunk instanceof Buffer)
                chunk = chunk.toString(this.CHARACTER_ENCODING);

            if (typeof chunk === 'string')
                this.#responseBuf += chunk;
            else
                throw new Error(`Stream at port ${this.#openPort.path} is in object mode which is currently not supported by the default data processor in the GenericMarlinFabricator class.`);

            // Split each line by the line splitter value
            const lines = this.#responseBuf.split(this.LINE_SPLITTER);

            if (this.#extractQ.length > 0) {
                // Because the last line is incomplete, it should not be checked using extractors just yet (hence the -1 to the length)
                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i];

                    const extractorCount = this.#extractQ.length;
                    let extractorsRan = 0;

                    while (extractorCount > extractorsRan) {
                        extractorsRan++;
                        /** @type {ResponseExtractor} */
                        // @ts-ignore It's impossible for this to be undefined since there has to be something in the array
                        const extractor = this.#extractQ.shift();

                        // If this extractor has timed out, then its response is no longer desired
                        if (extractor.status === 'timed-out')
                            break;
                        /** @todo By default, whenever a response from the fabricator is received, every extractor becomes 'in-progress' Will this cause issues? */
                        extractor.status = 'in-progress'; // A response has been received by the fabricator, so the extractor is now in-progress

                        if (extractor.regexes !== undefined) {
                            let extractorResult = null;

                            for (const regex of extractor.regexes) {
                                const currentMatch = regex.exec(line);
                                
                                if (currentMatch !== null) {
                                    if (currentMatch.groups === undefined)
                                        throw new Error(`The extractor ${extractor.regexes} did not provide named capture groups in its implementation. This behavior is not supported in the GenericMarlinFabricator class`);

                                    if (extractorResult === null)
                                        extractorResult = {};

                                    Object.assign(extractorResult, currentMatch.groups);
                                }
                            }

                            // If we get a result, then this extractor has found what it wanted
                            if (extractorResult !== null) {
                                // The result is stored as an object in the capture group
                                extractor.status = 'done';
                                extractor.callback({ status: 'processed', extractedResults: extractorResult });

                                if (ENABLE_ALL_FLAGS || SHOW_EXTRACTOR_RESULT)
                                    console.info(`The extractor ${extractor.regexes} returned '${Object.values(extractorResult)}' from '${line.trim()}'`);

                                break; /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                            } else {
                                // Else, the extractor didn't get what it wanted and should be re-added to the queue
                                this.#extractQ.push(extractor);

                                if (ENABLE_ALL_FLAGS || EXTRACTOR_FAILED_MATCH)
                                    console.info(`The extractor ${extractor.regexes} failed to match ${line}`);
                            }
                        } else {
                            if (ENABLE_ALL_FLAGS || MISSING_REGEX)
                                console.info(`An extractor sent to fabricator at port ${this.#openPort.path} has no RegEx and therefore won't extract any results from the line '${line}'`);

                            // If no regex is present, then it is assumed that this extractor wants to see 
                            // if the this.GCODE_PROCESSED_RESPONSE is present in the fabricator's response
                            if (this.#responseBuf.includes(this.GCODE_PROCESSED_RESPONSE)) {
                                extractor.status = 'done';
                                extractor.callback({ status: 'processed' });

                                break;  /** @todo End the loop since an extractor got a result. Check to see if this causes bugs */
                            } else {
                                // Else, the extractor didn't get what it wanted and should be re-added to the queue
                                this.#extractQ.push(extractor);
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

            // Because the last line is incomplete, it was not checked and therefore needs to be added as the start of the next  
            // All other lines are discarded as noise
            this.#responseBuf = lines[lines.length - 1];
            
            // Refresh the timeout tracking whether the fabricator is idle or not
            handleIdleTimeout.refresh();
        }

        /**
         * Handles the closing of the connection between the fabricator and the Node process
         * @param {Error} [err] Error object sent when an error causes the connection between the node process and the fabricator to end
         * @todo Fix the type for this particular error object. This object possesses the 'disconnected' property [VERY LOW PRIORITY]
         */
        const closeListener = (err) => {
            // Clear (remove) idle and hasBooted timeouts
            clearTimeout(handleIdleTimeout);
            clearTimeout(hasBootedTimeout);
            
            // End all existing extractors
            while (this.#extractQ.length > 0) {
                /** @type {ResponseExtractor} */
                // @ts-ignore
                const extractor = this.#extractQ.shift();

                extractor.callback({ status: 'fabricator-disconnected' });
                extractor.status = 'will-never-complete';
            }
            
            while (this.#instructQ.length > 0) {
                /** @type {InstructionExtractor} */
                // @ts-ignore
                const inst = this.#instructQ.shift();

                inst.extractor.callback({ status: 'fabricator-disconnected' });
                inst.extractor.status = 'will-never-complete';
            }
            
            // Remove the data event listener
            this.#openPort.removeListener('data', dataListener);

            /** @todo Ensure everything has been deleted else we have a memory leak */

            if (ENABLE_ALL_FLAGS || FABRICATOR_CONNECTION_CLOSED)
                console.info(`Fabricator at port ${this.#openPort.path} has closed its connection`);
        };
        
        this.#openPort
            .on('data', dataListener)
            .on('close', closeListener);
    }

    /**
     * Sends a G-Code instruction to a fabricator, and uses the extractor to return the result
     * If no response is received after this.RESPONSE_TIMEOUT, the status of the response will be 'timed-out' without any extracted results  
     * @param {string} instruction The G-Code instruction to send to the fabricator
     * @param {RegExp | RegExp[]} [extractorRegEx] The extractor to be used with this G-Code instruction
     * @param {boolean} [writeNow = false] Whether or not the G-Code instruction will be added to the queue or immediately sent to the fabricator (**Warning unsafe**)
     * @returns {Promise<FabricatorResponse>}
     */
    sendGCodeInstruction(instruction, extractorRegEx, writeNow = false) {
        /**
         * Internal function used to not write code twice
         * @param {function(FabricatorResponse): void} resolve
         */
        const _sendGCode = (resolve) => {
            // Ensure the connection to the fabricator isn't 
            // **WARNING** The Node SerialPort library doesn't update the .closed property when a fabricator unexpectedly disconnects
            /** However, the isOpen property seems to update @todo Why? */
            // **WARNING** The Node SerialPort library doesn't update .isOpen property when a stream is destroyed using the .destroy method
            /** However, the .closed property seems to update @todo Why? */
            if (this.#openPort.isOpen === false || this.#openPort.closed === true) {
                resolve({ status: 'fabricator-disconnected' });
                return; // Stop the execution of this function
            }
            
            if (extractorRegEx instanceof RegExp)
                extractorRegEx = [ extractorRegEx ];
            
            /** @type {ResponseExtractor} */
            const extractor = { regexes: extractorRegEx, status: 'started', callback: resolve };

            if (writeNow === false) {
                if (this.#extractQ.length === 0) {
                    // Add the extractor to the extract queue since it won't be automatically added
                    this.#extractQ.push(extractor);

                    // Immediately write to the port
                    this.#openPort.write(instruction, this.CHARACTER_ENCODING);
                } else {
                    this.#instructQ.push({
                        instruction: instruction,
                        extractor: extractor
                    });
                }

                if (this.#instructQ.length > this.ABNORMAL_REQUEST_AMOUNT)
                    if (ENABLE_ALL_FLAGS || MANY_GCODE_INSTRUCTIONS)
                        console.warn(`Fabricator at port ${this.#openPort.path} has over ${this.ABNORMAL_REQUEST_AMOUNT} G-Code instructions in its queue which is abnormal. The sendGCodeInstruction returns a promise that should be awaited.`);

            } else if (writeNow === true) {
                // Add the extractor to the extract queue since it won't be automatically added
                this.#extractQ.push(extractor);

                // Immediately write to the port
                this.#openPort.write(instruction, this.CHARACTER_ENCODING);

                if (ENABLE_ALL_FLAGS || SHOW_POTENTIALLY_UNSAFE_WRITES)
                    console.warn(`The G-Code instruction '${instruction.trim()}' was immediately written to port '${this.#openPort.path}'. This will likely lead to abnormal behavior`);
            }

            // The request times out after the timeout amount
            const responseTimeout = setTimeout(() => {
                // Used in the debugging code below to show the previous state of the extractor
                const previousState = extractor.status;

                // Only timeout when we never get a response from the fabricator, or the response is stale (it stopped responding after some time) 
                if (extractor.status === 'started' || extractor.status === 'stale') {
                    resolve({ status: 'timed-out'});
                    extractor.status = 'timed-out';
                    
                    if (ENABLE_ALL_FLAGS || SHOW_TIMED_OUT_INSTRUCTIONS)
                        console.warn(`The instruction ${instruction.trim()} with extractor ${extractorRegEx} timed out for fabricator on port ${this.#openPort.path}`);
                } else if (extractor.status === 'in-progress') {
                    extractor.status = 'stale'; // If the fabricator doesn't respond again, then this value won't update
                    responseTimeout.refresh();
                }

                if (ENABLE_ALL_FLAGS || SHOW_EXTRACTOR_STATE_AFTER_TIMEOUT)
                    console.info(`The state of extractor '${extractor.regexes}' for instruction '${instruction.trim()}' on port '${this.#openPort.path}' is '${extractor.status}' after response timeout. It was '${previousState}' before.`);
            }, this.RESPONSE_TIMEOUT);
        }

        return new Promise((resolve) => {
            // If it hasn't booted up yet, then wait the boot time
            if (this.#hasBooted === false)
                setTimeout(_sendGCode, this.BOOT_TIME, resolve);
            else
                _sendGCode(resolve);
        });
    }

    /**
     * Sends a dummy instruction to the fabricator. Uses this.DUMMY_INSTRUCTION
     * This is typically used to start the processing loop between the data processor and the fabricator
     * @param {boolean} [writeNow = true] If this dummy instruction should be added to the instruction queue or sent directly to the fabricator
     * @returns {Promise<FabricatorResponse>}
     */
    async sendDummyInstruction(writeNow = true) {
        if (this.#dummyInstructionBeingSent === false) {
            this.#dummyInstructionBeingSent = true;

            const response = await this.sendGCodeInstruction(this.DUMMY_INSTRUCTION, this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX, writeNow);

            this.#dummyInstructionBeingSent = false;

            if (response.status === 'processed' || response.status === 'timed-out')
                return response;

            if (ENABLE_ALL_FLAGS || UNHANDLED_STATES) {
                console.warn(`The sendDummyInstruction function has experienced an unhandled state! The status from the fabricator was ${response.status} instead of processed or timed-out`);
                // Some useful info
                console.warn(`Fabricator at port: ${this.#openPort.path}\nG-Code instruction sent: ${this.DUMMY_INSTRUCTION}\nExtractor used: ${this.DUMMY_INSTRUCTION_EXTRACTOR_REGEX}`);
            }

            return { status: 'unexpected-response' };
        } else {
            throw new Error(`A dummy instruction was already sent to fabricator at port ${this.#openPort.path}. Was this intentional?`);
        }
    }

    /**
     * Closes the serial connection
     * @returns {Promise<any>}
     */
    closeSerialConnection() {
        return new Promise((resolve) => {
            this.#openPort.close(resolve);
        });
    }

    // G-Code Instructions to communicate with fabricators
    // ..._INSTR is the G-Code instruction, 
    // ..._INSTR_EXTR is used to get results after the instruction is executed by the fabricator
    
    /**
     * Used to get firmware information from the fabricator
     * @readonly 
     * @type {string}
     */
    INFO_INSTR = 'M115\n';

    /**
     * Extracts FIRMWARE_NAME, MACHINE_TYPE, PROTOCOL_VERSION, and UUID from the output from the info instruction
     * Any of these variables can be 'undefined', so ensure that they exist
     * @readonly
     * @type {RegExp[]}
     */
    INFO_INSTR_EXTR = [
        /FIRMWARE_NAME:(?<firmwareName>.+)\s(?:SOURCE_CODE_URL|FIRMWARE_URL)/,
        /PROTOCOL_VERSION:(?<protocolVersion>.+)\s(?:MACHINE_TYPE)/,
        /MACHINE_TYPE:(?<machineType>.+)\s(?:EXTRUDER_COUNT)/,
        /UUID:(?<UUID>.+)\s?/
    ];

    /**
     * Returns the firmware information received from the info instruction
     * The extracted values are stored in an object with properties firmwareName, protocolVersion, machineType, and UUID
     * @returns {Promise<FabricatorResponse>}
     */
    getFirmwareInfo() {
        return this.sendGCodeInstruction(this.INFO_INSTR, this.INFO_INSTR_EXTR);
    }    
}