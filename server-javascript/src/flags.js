/** 
 * An object that contains all of the debug flags that can be set at runtime
 * 
 * A recommended preset has been set by default
 * @readonly
 */
export const DEBUG_FLAGS = {
    SHOW_EVERYTHING: false,
    NO_EXTRACTOR_PRESENT: true,
    EXTRA_DUMMY_INSTRUCTION: true,
    EXTRACTOR_FAILED_MATCH: false, // Annoying
    AUTOMATIC_EXTRACTOR_GIVEN: true,
    SHOW_EXTRACTOR_RESULT: true,
    SHOW_DUMMY_EXTRACTOR_RESPONSE: false, // Not important/Causes duplicate logs
};