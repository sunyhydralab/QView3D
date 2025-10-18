import WebSocket from 'ws';
import { EventEmitter } from 'events';
import logger from '../utils/logger.js';

export class WebSocketProxy extends EventEmitter {
  constructor(backends, routingMode) {
    super();
    this.backends = backends;
    this.mode = routingMode;
    this.clients = new Map();
    this.backendConnections = new Map();
  }

  handleConnection(clientWs, req) {
    const clientId = this.generateClientId();
    this.clients.set(clientId, clientWs);

    // Select backend WebSocket based on mode
    const backendWsUrl = this.selectBackendWs();
    logger.info(`Client ${clientId} connecting to ${backendWsUrl}`);

    try {
      const backendWs = new WebSocket(backendWsUrl);

      backendWs.on('open', () => {
        logger.info(`Backend connection established for client ${clientId}`);
        this.backendConnections.set(clientId, backendWs);
      });

      backendWs.on('error', (error) => {
        logger.error(`Backend WebSocket error for client ${clientId}: ${error.message}`);
      });

      // Forward client -> backend
      clientWs.on('message', (data) => {
        if (backendWs.readyState === WebSocket.OPEN) {
          const message = this.normalizeOutgoing(data);
          backendWs.send(message);
        }
      });

      // Forward backend -> client
      backendWs.on('message', (data) => {
        if (clientWs.readyState === WebSocket.OPEN) {
          const message = this.normalizeIncoming(data);
          clientWs.send(message);
        }
      });

      // Handle client disconnect
      clientWs.on('close', () => {
        logger.info(`Client ${clientId} disconnected`);
        if (backendWs.readyState === WebSocket.OPEN) {
          backendWs.close();
        }
        this.cleanup(clientId);
      });

      // Handle backend disconnect
      backendWs.on('close', () => {
        logger.warn(`Backend connection closed for client ${clientId}`);
        if (clientWs.readyState === WebSocket.OPEN) {
          clientWs.close();
        }
        this.cleanup(clientId);
      });

    } catch (error) {
      logger.error(`Failed to create backend connection: ${error.message}`);
      clientWs.close();
    }
  }

  selectBackendWs() {
    // Select WebSocket URL based on mode
    if (this.mode === 'javascript') {
      return `ws://localhost:${this.backends.javascript.ws_port}`;
    }
    // Default to Python (hybrid mode also uses Python for WS)
    return `ws://localhost:${this.backends.python.ws_port}`;
  }

  normalizeOutgoing(data) {
    // Client -> Backend normalization
    return data;
  }

  normalizeIncoming(data) {
    // Backend -> Client normalization
    return data;
  }

  generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  cleanup(clientId) {
    this.clients.delete(clientId);
    this.backendConnections.delete(clientId);
  }

  close() {
    // Close all connections
    for (const [id, ws] of this.clients) {
      ws.close();
    }
    for (const [id, ws] of this.backendConnections) {
      ws.close();
    }
    this.clients.clear();
    this.backendConnections.clear();
  }
}
