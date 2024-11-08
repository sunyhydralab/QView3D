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
    }
    // TODO: more events 
};

const printersMap = new Map();

wss.on('connection', (ws) => {
    console.log('WebSocket client connected');

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

httpServer.listen(8000, () => {
    console.log("WebSocket server is running on http://127.0.0.1:8000");
});
