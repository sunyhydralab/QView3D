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
    MISSING_REGEX: true, // Pollutes logs (but can be useful) 

};