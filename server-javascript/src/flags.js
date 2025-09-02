// A list of debug flags that can be imported by other modules
// A recommended default have been set but can be changed

// Can be used to enable all debug flags
export const ENABLE_ALL_FLAGS = false;

// Debug flags for
// Everything
// When the code doesn't support this particular state of the program, a log will be shown
export const UNHANDLED_STATES = true;

// Code that may or may not be necessary but was added just-in-case.
// If any of these logs appear, then the log should be deleted and the code it references should 
// be left alone because the log proves that that code path is reachable and therefore valid
export const NONEXISTENT_FUTURE = true;

// Debug flags for
// ../serial_communication/marlin_firmware/generic.js
export const NO_EXTRACTOR_PRESENT = true;

export const EXTRACTOR_FAILED_MATCH = true;

export const SHOW_EXTRACTOR_RESULT = true;

export const MANY_GCODE_INSTRUCTIONS = true;

export const SHOW_POTENTIALLY_UNSAFE_WRITES = true;

// Pollutes logs (but can be useful)
export const MISSING_REGEX = false;

export const FABRICATOR_IDLE = true;

export const FABRICATOR_CONNECTION_CLOSED = false;

// Whether or not to log when a request to a fabricator times out
export const SHOW_TIMED_OUT_INSTRUCTIONS = true;

// Pollutes logs (but can be useful)
export const SHOW_EXTRACTOR_STATE_AFTER_TIMEOUT = false;

export const FABRICATOR_CONNECTION_OPENED = true;

// Debug flags for
// ../serial_communication/marlin_firmware/helpers.js
export const SHOW_PICKED_DRIVER = true;

// Used to show when many timeouts occurred when trying to communicate with a printer
export const MANY_TIMEOUTS_OCCURRED = true;