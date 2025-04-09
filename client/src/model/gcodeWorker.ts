import * as GCodePreview from 'gcode-preview';

let preview: GCodePreview.WebGLPreview | null = null;
const originalConsoleWarn = console.warn;
const originalConsoleDebug= console.debug;
const originalConsoleInfo = console.info;

// Utility to suppress warnings
export function withConsoleSuppression<T>(fn: () => T): T {
    console.warn = () => {};
    console.debug = () => {};
    console.info = () => {};
    const result = fn();
    console.warn = originalConsoleWarn;
    console.debug = originalConsoleDebug;
    console.info = originalConsoleInfo;
    return result;
}

const processGCode = (gcode: string | string[], suppressWarnings: boolean = false) => {
    if (suppressWarnings) {
        withConsoleSuppression(() => preview?.processGCode(gcode));
    } else {
        preview?.processGCode(gcode);
    }
};

// Initialize GCodePreview with the OffscreenCanvas
self.onmessage = (event) => {
    const {type, payload} = event.data;
    // console.debug(type, payload)
    if (type === 'init') {
        const {canvas, options} = payload;

        preview = GCodePreview.init({
            canvas,
            ...options,
        });

        preview.camera.position.set(-200, 232, 200);
        preview.camera.lookAt(0, 0, 0);
        postMessage({type: 'initialized'});
    } else if (type === 'render') {
        const {gcode} = payload;
        try {
            processGCode(gcode, preview?.renderTubes ?? false);
            postMessage({type: 'renderComplete'});
        } catch (error) {
            postMessage({type: 'error', error: error});
        }
    }
};