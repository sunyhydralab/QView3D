/**
 * An object that contains all of the debug flags that can be set at runtime. true means enabled and false means disabled
 * @typedef {Object} DEBUG_FLAGS
 * @property {boolean} SHOW_EVERYTHING
 * @property {boolean} NO_EXTRACTOR_PRESENT
 * @property {boolean} EXTRA_DUMMY_INSTRUCTION
 */

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
    NO_NAMED_CAPTURE_GROUPS: true
};