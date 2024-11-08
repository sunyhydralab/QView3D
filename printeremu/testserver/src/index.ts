import { createServer } from "http";
import WebSocket from "ws";  // Import the WebSocket library

// Create an HTTP server
const httpServer = createServer();

// Create a WebSocket server (using the existing HTTP server)
const wss = new WebSocket.Server({ server: httpServer });

// Handle WebSocket client connections
wss.on('connection', (ws) => {
    console.log('WebSocket client connected');
    
    // Listen for incoming messages from WebSocket clients
    ws.on('message', (message) => {
        console.log('Received from WebSocket client:', message);
        // Echo the message back to the client
        ws.send('Hello from WebSocket server!');
    });

    // Handle WebSocket client disconnection
    ws.on('close', () => {
        console.log('WebSocket client disconnected');
    });
});

// Start the HTTP server (which is used by the WebSocket server)
httpServer.listen(8000, () => {
    console.log("WebSocket server is running on http://localhost:8000");
});
