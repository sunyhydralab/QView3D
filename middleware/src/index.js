import express from 'express';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { WebSocketServer, WebSocket } from 'ws';
import http from 'http';
import config from './config/backends.js';
import { routeMap } from './config/routes.js';
import logger from './utils/logger.js';

const app = express();
const PORT = config.middleware.port;

app.use(cors(config.corsOptions));

// Store current preferred backend (can be changed at runtime)
let preferredBackend = config.middleware.mode || 'python';

// Only parse JSON for specific middleware routes, not for proxy routes
app.get('/health', (req, res) => {
  res.json({
    middleware: 'healthy',
    mode: 'redundant-fallback',
    preferredBackend: preferredBackend,
    uptime: process.uptime()
  });
});

// API endpoint to change preferred backend
app.post('/api/set-backend', express.json(), (req, res) => {
  const { backend } = req.body;

  if (backend === 'python' || backend === 'javascript') {
    preferredBackend = backend;
    logger.info(`Preferred backend changed to: ${backend}`);
    res.json({ success: true, preferredBackend: backend });
  } else {
    res.status(400).json({ success: false, error: 'Invalid backend. Must be "python" or "javascript"' });
  }
});

app.get('/api/get-backend', (req, res) => {
  res.json({ preferredBackend });
});

function matchRoute(path, pattern) {
  return path === pattern || path.startsWith(pattern + '/');
}

function getPrimaryBackend(path) {
  // Check if route has a specific backend requirement
  for (const [pattern, backendName] of Object.entries(routeMap)) {
    if (matchRoute(path, pattern)) {
      if (backendName === 'javascript') {
        return config.backends.javascript;
      }
      if (backendName === 'python') {
        return config.backends.python;
      }
      // If 'either', use the preferred backend
      if (backendName === 'either') {
        return preferredBackend === 'python' ? config.backends.python : config.backends.javascript;
      }
    }
  }
  // Default to preferred backend
  return preferredBackend === 'python' ? config.backends.python : config.backends.javascript;
}

function getFallbackBackend(primary) {
  return primary === config.backends.javascript
    ? config.backends.python
    : config.backends.javascript;
}

async function tryBackend(backend, req, res) {
  return new Promise((resolve) => {
    let resolved = false;

    const proxy = createProxyMiddleware({
      target: backend.url,
      changeOrigin: true,
      timeout: 5000,
      onError: (err, req, res) => {
        if (!resolved) {
          resolved = true;
          logger.error(`${backend.name} failed: ${err.message}`);
          resolve(false);
        }
      },
      onProxyRes: (proxyRes) => {
        if (!resolved) {
          resolved = true;
          logger.info(`${backend.name} responded with ${proxyRes.statusCode}`);
          resolve(true);
        }
      }
    });

    proxy(req, res, (err) => {
      if (err && !resolved) {
        resolved = true;
        logger.error(`${backend.name} middleware error: ${err.message}`);
        resolve(false);
      }
    });
  });
}

app.use(async (req, res, next) => {
  const primary = getPrimaryBackend(req.path);
  const fallback = getFallbackBackend(primary);

  logger.info(`Request: ${req.method} ${req.path} -> trying ${primary.name}`);

  const success = await tryBackend(primary, req, res);

  if (!success && !res.headersSent) {
    logger.info(`Fallback to ${fallback.name}`);
    const fallbackSuccess = await tryBackend(fallback, req, res);

    if (!fallbackSuccess && !res.headersSent) {
      res.status(503).json({ error: 'All backends unavailable' });
    }
  }
});

const server = http.createServer(app);
server.setMaxListeners(50); // Increase listener limit to avoid warnings
const wss = new WebSocketServer({ server });

wss.on('connection', (ws, req) => {
  logger.info('WebSocket connection established');

  const primary = getPrimaryBackend(req.url);
  const fallback = getFallbackBackend(primary);

  // Try to connect to primary backend WebSocket
  const tryConnect = (backend) => {
    const wsPort = backend.ws_port || (backend.url.includes(':8000') ? 8001 : 3001);
    const wsUrl = `ws://localhost:${wsPort}`;

    const backendWs = new WebSocket(wsUrl);
    let connected = false;

    backendWs.on('open', () => {
      connected = true;
      logger.info(`WebSocket connected to ${backend.name} on port ${wsPort}`);

      ws.on('message', (data) => {
        if (backendWs.readyState === WebSocket.OPEN) {
          backendWs.send(data);
        }
      });

      backendWs.on('message', (data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });
    });

    backendWs.on('error', (err) => {
      if (!connected && backend === primary) {
        logger.error(`${backend.name} WebSocket failed: ${err.message}, trying fallback`);
        tryConnect(fallback);
      } else {
        logger.error(`WebSocket error: ${err.message}`);
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
    });

    ws.on('close', () => {
      if (backendWs.readyState === WebSocket.OPEN) {
        backendWs.close();
      }
    });

    backendWs.on('close', () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    });
  };

  tryConnect(primary);
});

server.listen(PORT, () => {
  logger.info(`Middleware running on port ${PORT}`);
  logger.info(`Primary: JavaScript (${config.backends.javascript.url})`);
  logger.info(`Fallback: Python (${config.backends.python.url})`);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
process.on('SIGINT', () => server.close(() => process.exit(0)));
