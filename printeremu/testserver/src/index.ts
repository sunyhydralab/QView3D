import { createServer } from "http";
import WebSocket from "ws";

const httpServer = createServer();

const wss = new WebSocket.Server({ server: httpServer });

const eventHandlers = {
    emuprintconnect: (ws, data) => {
        const printerId = data.Id;
        const printerInfo = data;

        if (!printerId) {
            console.log('No printerId provided, cannot register printer');
            ws.send(JSON.stringify({ event: 'error', message: 'No printerId provided' }));
            return;
        }
        printersMap.set(printerId, { ws, printerInfo });

        console.log(`Printer connected with ID: ${printerId}`);
        ws.send(JSON.stringify({ event: 'info', message: 'Successfully registered printer with ID ' + printerId + ' and name ' + printerInfo.Name }));
    },
    ping: (ws, data) => {
        // do nothing!
        // console.log('Received ping event');

        if (data.data !== 'alive'){
            ws.send(JSON.stringify({ event: 'error', message: 'Invalid ping data' }));
        }
    },
    send_gcode: (ws, data) => {
        // Handle G-code command from the client here
        console.log(`Sent G-code: ${data}`);
    },
    gcode_response: (ws, data) => {
        console.log(`Received G-code response: ${data}`);
    }
};

function sendGCodeCommands(ws) {
    const gcodeCommands = [
        "G28",  // Home all axes
        "G1 X10 Y10 Z10 F1500",  // Move to X:10 Y:10 Z:10
        "G1 X20 Y20 Z20 F1500",  // Move to X:20 Y:20 Z:20
        "G1 Z0",  // Move to Z:0
        "M104 S200",  // Set extruder temperature
        "M140 S60",  // Set bed temperature
        "M107",  // Turn off fan
        "M155 S1", // get temps
        "M155 S0", // turn off
    ];

    gcodeCommands.forEach((gcode, index) => {
        setTimeout(() => {
            console.log(`Sending G-code command: ${gcode}`);
            ws.send(JSON.stringify({
                event: 'send_gcode',
                data: { 
                    printerid: '10000', 
                    gcode: gcode 
                }
            }));
        }, index * 2000);  // Send every 2 seconds
    });
}

const printersMap = new Map();

wss.on('connection', (ws) => {
    console.log('WebSocket client connected');

    // Send a "ping" or "gcode" after a connection is established
    setTimeout(() => {
        ws.send(JSON.stringify({
            event: 'ping',
            data: 'alive'
        }));
    }, 1000); // Send ping after 1 second

    // Send a series of G-code commands after the initial ping
    setTimeout(() => {
        sendGCodeCommands(ws);  // Call sendGCodeCommands function explicitly here
    }, 3000);  // Start sending G-code after 3 seconds

    ws.on('message', (message) => {
        let parsedMessage;

        try {
            parsedMessage = JSON.parse(message);
        } catch (err) {
            console.log('Failed to parse message:', err);
            return;
        }

        const { event, data } = parsedMessage;

        const handler = eventHandlers[event];

        if (handler) {
            handler(ws, data);
        } else {
            console.log('Unknown event type:', event);
            ws.send(JSON.stringify({ event: 'error', message: 'Unknown event type' }));
        }
    });

    ws.on('close', () => {
        console.log('WebSocket client disconnected');

        for (const [printerId, printerData] of printersMap) {
            if (printerData.ws === ws) {
                printersMap.delete(printerId);
                console.log(`Printer disconnected and removed with ID: ${printerId}`);
                break;
            }
        }
    });
});

httpServer.listen(8001, () => {
    console.log("WebSocket server is running on http://127.0.0.1:8001");
});