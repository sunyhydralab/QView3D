import { VirtualPrinter } from './VirtualPrinter.js';

const PRINTER_MODELS = {
    'PrusaMK4': 'Prusa MK4',
    'PrusaMK3': 'Prusa i3 MK3',
    'Ender3': 'Ender 3'
};

async function startEmulator() {
    const args = process.argv.slice(2);
    const modelArg = args[0] || 'PrusaMK4';
    const portArg = args[1] || 'EMU0';
    const wsUrl = args[2] || 'ws://localhost:8001';

    const model = PRINTER_MODELS[modelArg] || modelArg;

    console.log('=== QView3D Virtual Printer Emulator ===');
    console.log(`Model: ${model}`);
    console.log(`Port: ${portArg}`);
    console.log(`Backend: ${wsUrl}`);
    console.log('========================================\n');

    const printer = new VirtualPrinter(model, portArg);

    try {
        await printer.connect(wsUrl);
        console.log('Emulator running. Press Ctrl+C to stop.\n');

        // Keep process alive
        process.on('SIGINT', () => {
            console.log('\nShutting down emulator...');
            printer.disconnect();
            process.exit(0);
        });
    } catch (error) {
        console.error('Failed to start emulator:', error);
        process.exit(1);
    }
}

startEmulator();
