import { SerialPort } from './serialport.js';
import { log } from './util/log.js';
import { EventEmitter } from 'node:events';
import { GCodeScript } from './gcode_script.js';

// Character encoding used in Marlin compatible 3D printers
const MARLIN_PROTOCOL_ENCODING = 'utf-8';

// Used to differentiate between ambiguous errors and errors thrown by printer operations
export class PrinterError extends Error {};

export const PrinterState = {
    NOT_CONNECTED: 0,
    READY: 1,
    PRINTING: 2,
    CONNECTING: 3,
    PAUSED: 4,
    ERROR: 5
};

const PrinterEvent = {
    STATE_CHANGE: 'stateChange'
};

const VALID_PRINTER_STATES = Object.values(PrinterState);

const VALID_BAUD_RATES = [115200, 250000, 230400, 57600, 38400, 19200, 9600];

const SERIAL_PRINT_COMMAND = 'M118 E1 Hello, world!\n';

/**
 * Class used to communicate with {@link https://github.com/MarlinFirmware/Marlin Marlin firmware} compatible 3D printers
 */
export class Printer {
    #state;
    // Used to hold incomplete responses from the printer
    #dataBuffer;
    #currentScript;
    #serialPort;
    // Used to call any callback functions that are listening for events from this printer
    #eventEmitter;

    constructor() {
        this.#eventEmitter = new EventEmitter();
        this.#setState(PrinterState.NOT_CONNECTED);
        this.#dataBuffer = '';
        this.#serialPort = undefined;
        this.#currentScript = undefined;
    }
    
    #sendGcodeCommand(gcodeCommand) {
        /** @todo Figure out the errors that can occur. Maybe use .isOpen to determine if the port is still open? */
        try {
            this.#serialPort.write(gcodeCommand, MARLIN_PROTOCOL_ENCODING);
        } catch (err) {
            throw new PrinterError(`Failed to send a command to the 3D printer at port "${this.#serialPort.path}"`, { cause: err });
        }
        
        log(
            `${this.#serialPort.path} ${gcodeCommand.replace('\n', '\\n')}`,
            'printer.js',
            'COMMAND_SENT_TO_PRINTER'
        );
    }
    
    /** 
     * Function used to listen and process data coming from a connected 3D printer
     * Assumes to be a callback function to the {@link https://nodejs.org/docs/latest-v18.x/api/stream.html#event-data 'data'} event
     */
    #portListener(dataFromPort) {
        // Interpret the raw binary coming from the port as UTF-8 (or whatever MARLIN_PROTOCOL_ENCODING is) encoded strings
        if (dataFromPort instanceof Buffer)
            dataFromPort = dataFromPort.toString(MARLIN_PROTOCOL_ENCODING);
        
        // The response from the printer may not be complete so we must store the current response in a buffer
        // When we receive more data, we'll stitch the content together to create a complete response
        if (typeof dataFromPort === 'string')
            this.#dataBuffer += dataFromPort;
        else
            throw new Error(`Stream at port "${this.#serialPort?.path}" is in object mode which is not supported`);

        // Ensure the printer isn't paused
        if (this.#state !== PrinterState.PAUSED) {
            // Each complete response from the printer must be processed by the server
            // a complete response is UTF-8 (or whatever MARLIN_PROTOCOL_ENCODING is) encoded strings ending with a newline 
            // sometimes the printer will send multiple complete responses at once so we split each response by the newline
            const outputLines = this.#dataBuffer.split('\n');
            
            // But, the last line doesn't end with a newline so we won't process it (outputLines.length - 1)
            const incompleteLine = outputLines[outputLines.length - 1];
            
            /** 
             * @todo !! When the printer is paused, it could receive multiple "ok's" which would cause
             * this loop to send multiple G-code commands at once. Doing this may cause the printer
             * to ignore some of the commands being sent to it. It may also be hard to detect because
             * very little commands would be lost...
             * One solution is to send only 1 command when we receive multiple "ok's"
             * @todo This solution is in use. Ensure that it properly works!
             */
            let commandSent = false;
            
            for (let i = 0; i < outputLines.length - 1; i++) {
                const currentLine = outputLines[i];
                //## Handle progress update
                /** @todo */
                
                //## When we receive an OK
                if (currentLine.startsWith('ok') && currentLine.length === 2) {
                    // Send the next G-Code command if the printer is PRINTING
                    if (this.#state === PrinterState.PRINTING) {
                        const gScript = this.#currentScript;

                        if (!gScript.reachedEndOfScript()) {
                            // More G-code to send
                            // Don't spam the printer if we already sent a command for a previous 'ok'
                            if (commandSent === false) {
                                const nextCommand = gScript.nextGcodeCommand();
                                this.#sendGcodeCommand(nextCommand);
                                commandSent = true;
                            }
                        } else {
                            // No more G-code to send
                            log(
                                `Printer at port "${this.#serialPort?.path}" finished printing`,
                                'printer.js',
                                'PRINTER_JOB_COMPLETED'
                            );
                            this.#setState(PrinterState.READY);

                            if (incompleteLine.length !== 0) {
                                log(
                                    `The 3D printer at port "${this.#serialPort?.path}" had the content "${this.#dataBuffer}" in its buffer`,
                                    'printer.js',
                                    'NON_EMPTY_OUTPUT_BUFFER_ON_JOB_COMPLETE'
                                );
                            }
                        }
                    }
                }
        
                //## Handle temperature change
                /** @todo */
            }
            
            log(
                `${this.#serialPort?.path} ${this.#dataBuffer.replaceAll('\n', '\\n')}`,
                'printer.js',
                'RESPONSE_FROM_PRINTER'
            );
            
            // Because the last line is not a complete response, we'll store it in our buffer 
            // and concatenate it with the next response from the printer
            // All other lines were processed so they are discarded
            this.#dataBuffer = incompleteLine;
        } else {
            // Because the printer is paused, none of the responses from the printer are being processed
            // Therefore, the buffer won't be overwritten (this.#dataBuffer != incompleteLine)
            log(
                `${this.#serialPort.path} ${this.#dataBuffer.replaceAll('\n', '\\n')}`,
                'printer.js',
                'UNPROCESSED_RESPONSE'
            );
        }
        
    }
    
    /** Function used to cleanly disconnect from a printer */
    #closeListener(err) {
        if (err instanceof DisconnectedError) {
            /** @todo handle disconnect error */
            log(
                err.message,
                'printer.js',
                'PRINTER_DISCONNECT_ERROR'
            );
        }

        // Clear properties and set state to NOT_CONNECTED
        this.#serialPort = undefined;
        this.#dataBuffer = '';
        this.#setState(PrinterState.NOT_CONNECTED);

        // The printer will automatically turn off its hotends based on its hotend idle timeout (https://marlinfw.org/docs/gcode/M086.html)
    }
    
    #setState(newState) {
        if (VALID_PRINTER_STATES.includes(newState)) {
            this.#state = newState;
            this.#eventEmitter.emit(PrinterEvent.STATE_CHANGE, newState);
            
            log(
                `The state of printer at port "${this.#serialPort?.path ?? 'NOT_CONNECTED_TO_PORT'}" is now "${newState}"`,
                'printer.js',
                'PRINTER_STATE_CHANGE'
            );
        } else {
            throw new Error(`${newState} is not a valid printer state. Use the PrinterState object declared above to see the valid printer states`);
        }
    }
    
    /**
     * Sets the serial port to communicate with and baudRate to use. Baud rate defaults to 115200b/s
     * If the printer is printing or paused, this will throw a `PrinterError`
     * When the connection to the printer is established, `connectedCallback` is called
     */
    setSerialPort(serialPortLocation, connectedCallback, baudRate = 115200) {
        if (!VALID_BAUD_RATES.includes(baudRate))
            throw new Error(`${baudRate} is not a valid or supported baud rate`);
            
        if (this.#serialPort instanceof SerialPort) {
            if (this.#state === PrinterState.PRINTING || this.#state === PrinterState.PAUSED)
                throw new PrinterError(`Cannot set serial port because the printer at port "${this.#serialPort.path}" is currently printing`);

            this.#serialPort.close();
        }
        
        this.#setState(PrinterState.CONNECTING);

        this.#serialPort = new SerialPort({ path: serialPortLocation, baudRate: baudRate}, _ => {
            /** I believe this function is called when the SerialPort class has connected to the serial port @todo Double check */
            /** @todo handle any errors that occur during opening the serial port */

            this.#setState(PrinterState.READY);
            
            if (typeof connectedCallback === 'function')
                connectedCallback.call(this);
            else if (typeof connectedCallback !== 'undefined')
                throw new TypeError(`connectedCallback is meant to be a function or undefined, not ${typeof connectedCallback}`);
        });
        
        this.#serialPort
            .on('data', this.#portListener.bind(this))
            .on('close', this.#closeListener.bind(this));
    }
    
    /**
     * Sets the G-Code script for the printer to start printing
     * If the printer is printing or paused, this will throw a `PrinterError`
     */
    setGcodeScript(gcodeScript) {
        if (!(gcodeScript instanceof GCodeScript))
            throw new TypeError(`setGcodeScript expected a GCodeScript object, not a "${typeof gcodeScript}"`);
        
        if (this.#state === PrinterState.PAUSED || this.#state === PrinterState.PRINTING)
            throw new PrinterError(`Printer at port ${this.#serialPort.path} is already printing a script. This process must be stopped before setting another script`);
        
        this.#currentScript = gcodeScript;
    }
    
    /**
     * If the printer is printing, paused, not connected or connecting to a port, this will throw a `PrinterError`
     * Also, if no script has been set, then a `PrinterError` will be thrown
     */
    startPrint() {
        if (this.#state === PrinterState.READY) {
            if (typeof this.#currentScript === 'undefined')
                throw new PrinterError(`Printer at port ${this.#serialPort.path} has no script set`);
            
            log(
                `Printer "${this.#serialPort.path}" has started G-Code script ${this.#currentScript.name} `, 
                'printer.js', 
                'PRINTER_JOB_STARTED'
            );
            
            this.#setState(PrinterState.PRINTING);
            this.#sendGcodeCommand(this.#currentScript.nextGcodeCommand());
        } else if (this.#state === PrinterState.NOT_CONNECTED || this.#state === PrinterState.CONNECTING) {
            throw new PrinterError('A G-Code script cannot be printed because the connection to the printer hasn\'t been established yet'); 
        } else if (this.#state === PrinterState.PRINTING || this.#state === PrinterState.PAUSED) {
            /** @todo Should we throw an error for this? (Errors crash the program) */
            throw new PrinterError(`Printer at port "${this.#serialPort.path}" has already started printing the script`);
        }
    }
    
    /** If the printer is not printing or already paused, then this will throw a `PrinterError` */
    pausePrint() {
        if (this.#state === PrinterState.PRINTING) {
            this.#setState(PrinterState.PAUSED);
        } else if (this.#state === PrinterState.PAUSED) {
            /** @todo Should we throw an error for this? */ 
            throw new PrinterError(`Printer at port "${this.#serialPort.path}" is already paused`);
        } else {
            throw new PrinterError(`Attempted to pause printer at port "${this.#serialPort.path}" when it's not printing`);
        }
    }
    
    stopPrint() {
        throw new Error('Function not implemented');
    }
    
    continuePrint() {
        if (this.#state === PrinterState.PAUSED) {
            this.#setState(PrinterState.PRINTING);
            // Send this command to the printer so that we get an immediate response 
            // Note: portListener only processes responses when the printer sends them
            // Therefore, to get portListener to process responses, the printer needs to
            // send a response (hence the SERIAL_PRINT_COMMAND)
            this.#sendGcodeCommand(SERIAL_PRINT_COMMAND);
        } else if (this.#state === PrinterState.PRINTING) {
            /** @todo Should we throw an error for this? */
            throw new PrinterError(`Printer at port "${this.#serialPort.path}" is already printing so continuing it makes no sense`);
        } else {
            throw new PrinterError(`Printer at port "${this.#serialPort?.path}" is not paused. Therefore, it cannot be continued`);
        }
    }

    closeSerialPort() {
        this.#serialPort.close();
    }

    onTempChange(callback) {
        throw new Error('Function not implemented');
    }

    onProgressUpdate(callback) {
        throw new Error('Function not implemented');
    }
    
    /** Calls `callback` with the new state that the printer has changed to */
    onStateChange(callback) {
        if (typeof callback !== 'function')
            throw new TypeError(`Callbacks are functions that are called when an event occurs. Not a "${typeof callback}"`);

        this.#eventEmitter.on(PrinterEvent.STATE_CHANGE, callback);
    }

    getCurrentScript() {
        throw new Error('Function not implemented');
    }

    getModelName() {
        throw new Error('Function not implemented');
    }

    getCurrentState() {
        return this.#state;
    }

}
