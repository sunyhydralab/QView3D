import express from 'express';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { WebSocketServer, WebSocket } from 'ws';
import http from 'http';
import config from './config/backends.js';
import logger from './utils/logger.js';

const app = express();
const PORT = config.middleware.port;

app.use(cors(config.corsOptions));

// Current selected backend (loaded from config)
let selectedBackend = config.middleware.mode || 'python';

// Get the active backend configuration
function getActiveBackend() {
  return selectedBackend === 'python' ? config.backends.python : config.backends.javascript;
}

// Health check endpoint
app.get('/health', (req, res) => {
  const backend = getActiveBackend();
  res.json({
    middleware: 'healthy',
    selectedBackend: selectedBackend,
    backendUrl: backend.url,
    uptime: process.uptime()
  });
});

// API endpoint to change backend (requires server restart)
app.post('/api/set-backend', express.json(), (req, res) => {
  const { backend } = req.body;

  if (backend === 'python' || backend === 'javascript') {
    selectedBackend = backend;
    logger.info(`Backend changed to: ${backend} (requires server restart to take effect)`);
    res.json({
      success: true,
      selectedBackend: backend,
      message: 'Backend preference saved. Restart the server to apply changes.'
    });
  } else {
    res.status(400).json({ success: false, error: 'Invalid backend. Must be "python" or "javascript"' });
  }
});

// Get current backend
app.get('/api/get-backend', (req, res) => {
  res.json({
    selectedBackend,
    backendUrl: getActiveBackend().url
  });
});

// Proxy all requests to the selected backend
app.use((req, res, next) => {
  const backend = getActiveBackend();

  logger.info(`Request: ${req.method} ${req.path} -> ${backend.name}`);

  const proxy = createProxyMiddleware({
    target: backend.url,
    changeOrigin: true,
    timeout: 10000,
    onError: (err, req, res) => {
      logger.error(`${backend.name} failed: ${err.message}`);
      if (!res.headersSent) {
        res.status(503).json({
          error: `${backend.name} backend unavailable`,
          details: err.message
        });
      }
    },
    onProxyRes: (proxyRes) => {
      logger.info(`${backend.name} responded with ${proxyRes.statusCode}`);
    }
  });

  proxy(req, res, next);
});

// Create HTTP server
const server = http.createServer(app);
server.setMaxListeners(50);

// WebSocket server
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
  logger.info('WebSocket connection established');

  const backend = getActiveBackend();
  const wsPort = backend.ws_port;
  const wsUrl = `ws://localhost:${wsPort}`;

  const backendWs = new WebSocket(wsUrl);

  backendWs.on('open', () => {
    logger.info(`WebSocket connected to ${backend.name} on port ${wsPort}`);

    // Forward messages from client to backend
    ws.on('message', (data) => {
      if (backendWs.readyState === WebSocket.OPEN) {
        backendWs.send(data);
      }
    });

    // Forward messages from backend to client
    backendWs.on('message', (data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
      }
    });
  });

  backendWs.on('error', (err) => {
    logger.error(`WebSocket error connecting to ${backend.name}: ${err.message}`);
    if (ws.readyState === WebSocket.OPEN) {
      ws.close(1011, `Backend ${backend.name} unavailable`);
    }
  });

  // Clean up on client disconnect
  ws.on('close', () => {
    if (backendWs.readyState === WebSocket.OPEN || backendWs.readyState === WebSocket.CONNECTING) {
      backendWs.close();
    }
  });

  // Clean up on backend disconnect
  backendWs.on('close', () => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.close();
    }
  });
});

server.listen(PORT, () => {
  const backend = getActiveBackend();
  logger.info(`Middleware running on port ${PORT}`);
  logger.info(`Active Backend: ${backend.name} (${backend.url})`);
  logger.info(`WebSocket Port: ${backend.ws_port}`);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
process.on('SIGINT', () => server.close(() => process.exit(0)));
