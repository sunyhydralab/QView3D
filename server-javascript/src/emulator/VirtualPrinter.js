import WebSocket from 'ws';

/**
 * Virtual printer emulator that connects to Python backend via WebSocket
 * Simulates a Marlin-based 3D printer responding to G-code commands
 */
export class VirtualPrinter {
    constructor(model = 'PrusaMK4', port = 'EMU0') {
        this.model = model;
        this.port = port;
        this.position = { x: 0, y: 0, z: 0, e: 0 };
        this.temperature = { hotend: 20, bed: 20 };
        this.targetTemp = { hotend: 0, bed: 0 };
        this.fan = 0;
        this.printing = false;
        this.homing = false;

        // WebSocket connection to Python backend
        this.ws = null;
        this.connected = false;
    }

    connect(url = 'ws://localhost:8001') {
        return new Promise((resolve, reject) => {
            this.ws = new WebSocket(url);

            this.ws.on('open', () => {
                console.log(`[${this.model}] Connected to QView3D backend`);

                // Send initial connection message with port info
                const handshake = JSON.stringify({
                    port: this.port,
                    Name: this.model,
                    Hwid: `EMU_VID:PID=FFFF:${this.port}`
                });
                this.ws.send(handshake);

                this.connected = true;
                resolve();
            });

            this.ws.on('message', (data) => {
                const message = data.toString();
                const response = this.processGCode(message);
                if (response) {
                    this.ws.send(response);
                }
            });

            this.ws.on('close', () => {
                console.log(`[${this.model}] Disconnected from backend`);
                this.connected = false;
            });

            this.ws.on('error', (error) => {
                console.error(`[${this.model}] WebSocket error:`, error);
                reject(error);
            });
        });
    }

    processGCode(gcode) {
        gcode = gcode.trim();

        // Remove comments
        const command = gcode.split(';')[0].trim();
        if (!command) return 'ok\n';

        console.log(`[${this.model}] Processing: ${command}`);

        // Movement commands
        if (command.startsWith('G0') || command.startsWith('G1')) {
            return this.handleMovement(command);
        }

        // Homing
        else if (command.startsWith('G28')) {
            return this.handleHoming(command);
        }

        // Set hotend temperature
        else if (command.startsWith('M104')) {
            return this.handleSetHotendTemp(command);
        }

        // Wait for hotend temperature
        else if (command.startsWith('M109')) {
            return this.handleWaitHotendTemp(command);
        }

        // Set bed temperature
        else if (command.startsWith('M140')) {
            return this.handleSetBedTemp(command);
        }

        // Wait for bed temperature
        else if (command.startsWith('M190')) {
            return this.handleWaitBedTemp(command);
        }

        // Get temperature
        else if (command.startsWith('M105')) {
            return this.handleGetTemperature();
        }

        // Get firmware info
        else if (command.startsWith('M115')) {
            return this.handleGetFirmwareInfo();
        }

        // Fan control
        else if (command.startsWith('M106')) {
            return this.handleSetFan(command);
        }
        else if (command.startsWith('M107')) {
            this.fan = 0;
            return 'ok\n';
        }

        // Get position
        else if (command.startsWith('M114')) {
            return this.handleGetPosition();
        }

        // Generic echo/debug
        else if (command.startsWith('M118')) {
            const message = command.substring(4).trim();
            return `echo:${message}\nok\n`;
        }

        // Default response
        return 'ok\n';
    }

    handleMovement(command) {
        const parts = command.split(' ');
        for (const part of parts) {
            if (part.startsWith('X')) this.position.x = parseFloat(part.substring(1));
            if (part.startsWith('Y')) this.position.y = parseFloat(part.substring(1));
            if (part.startsWith('Z')) this.position.z = parseFloat(part.substring(1));
            if (part.startsWith('E')) this.position.e = parseFloat(part.substring(1));
        }
        return 'ok\n';
    }

    handleHoming(command) {
        this.homing = true;

        // Check which axes to home
        if (command.includes('X') || command.length <= 4) this.position.x = 0;
        if (command.includes('Y') || command.length <= 4) this.position.y = 0;
        if (command.includes('Z') || command.length <= 4) this.position.z = 0;

        // Simulate homing delay
        setTimeout(() => {
            this.homing = false;
        }, 1000);

        return 'ok\n';
    }

    handleSetHotendTemp(command) {
        const match = command.match(/S(\d+)/);
        if (match) {
            this.targetTemp.hotend = parseInt(match[1]);
            // Simulate gradual heating
            this.simulateHeating('hotend');
        }
        return 'ok\n';
    }

    handleWaitHotendTemp(command) {
        const match = command.match(/S(\d+)/);
        if (match) {
            this.targetTemp.hotend = parseInt(match[1]);
            this.simulateHeating('hotend');
        }
        // In real implementation, would wait until temp reached
        return 'ok\n';
    }

    handleSetBedTemp(command) {
        const match = command.match(/S(\d+)/);
        if (match) {
            this.targetTemp.bed = parseInt(match[1]);
            this.simulateHeating('bed');
        }
        return 'ok\n';
    }

    handleWaitBedTemp(command) {
        const match = command.match(/S(\d+)/);
        if (match) {
            this.targetTemp.bed = parseInt(match[1]);
            this.simulateHeating('bed');
        }
        return 'ok\n';
    }

    handleGetTemperature() {
        return `ok T:${this.temperature.hotend.toFixed(1)}/${this.targetTemp.hotend} B:${this.temperature.bed.toFixed(1)}/${this.targetTemp.bed}\n`;
    }

    handleGetFirmwareInfo() {
        const info = [
            'FIRMWARE_NAME:Marlin 2.1.2 (Virtual)',
            `MACHINE_TYPE:${this.model}`,
            'EXTRUDER_COUNT:1',
            'UUID:virtual-emulator-001'
        ].join(' ');
        return `${info}\nok\n`;
    }

    handleSetFan(command) {
        const match = command.match(/S(\d+)/);
        if (match) {
            this.fan = parseInt(match[1]);
        }
        return 'ok\n';
    }

    handleGetPosition() {
        return `X:${this.position.x.toFixed(2)} Y:${this.position.y.toFixed(2)} Z:${this.position.z.toFixed(2)} E:${this.position.e.toFixed(2)}\nok\n`;
    }

    simulateHeating(component) {
        const interval = setInterval(() => {
            const current = this.temperature[component];
            const target = this.targetTemp[component];

            if (Math.abs(current - target) < 1) {
                this.temperature[component] = target;
                clearInterval(interval);
            } else {
                // Gradually approach target temperature
                const delta = (target - current) * 0.1;
                this.temperature[component] += delta;
            }
        }, 500);
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}
