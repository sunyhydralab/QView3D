/** 
 * An object that contains all of the debug flags that can be set at runtime
 * 
 * A recommended preset has been set by default
 * @readonly
 */
export const DEBUG_FLAGS = {
    SHOW_EVERYTHING: false,
    NO_EXTRACTOR_PRESENT: true,
    EXTRACTOR_FAILED_MATCH: true,
    SHOW_EXTRACTOR_RESULT: true,
    MANY_GCODE_INSTRUCTIONS: true,
    SHOW_POTENTIALLY_UNSAFE_WRITES: true,
    UNHANDLED_STATES: true, // When the code doesn't support this particular state of the program, a log will be shown
    MISSING_REGEX: false, // Pollutes logs (but can be useful)
    FABRICATOR_IDLE: true,
    NONEXISTENT_FUTURE: true, // Code that may or may not be necessary but was added just-in-case.
                              // If any of these logs appear, then the log should be deleted and the code it references should 
                              // be left alone because the log proves that that code path is reachable and therefore valid
    FABRICATOR_CLOSED: true,
    SHOW_TIMED_OUT_INSTRUCTIONS: true, // Whether or not to log when a request to a fabricator times out
    SHOW_EXTRACTOR_STATE_AFTER_TIMEOUT: false, // Pollutes logs (but can be useful)
};