import express from 'express';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import WebSocket from 'ws';
import http from 'http';
import config from './config/backends.js';
import { routeMap } from './config/routes.js';
import logger from './utils/logger.js';

const app = express();
const PORT = config.middleware.port;

app.use(cors(config.corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.get('/health', (req, res) => {
  res.json({
    middleware: 'healthy',
    mode: 'redundant-fallback',
    uptime: process.uptime()
  });
});

function matchRoute(path, pattern) {
  return path === pattern || path.startsWith(pattern + '/');
}

function getPrimaryBackend(path) {
  for (const [pattern, backendName] of Object.entries(routeMap)) {
    if (matchRoute(path, pattern)) {
      if (backendName === 'either' || backendName === 'javascript') {
        return config.backends.javascript;
      }
      if (backendName === 'python') {
        return config.backends.python;
      }
    }
  }
  return config.backends.javascript;
}

function getFallbackBackend(primary) {
  return primary === config.backends.javascript
    ? config.backends.python
    : config.backends.javascript;
}

async function tryBackend(backend, req, res) {
  return new Promise((resolve) => {
    const proxy = createProxyMiddleware({
      target: backend.url,
      changeOrigin: true,
      timeout: 5000,
      onError: (err) => {
        logger.error(`${backend.name} failed: ${err.message}`);
        resolve(false);
      },
      onProxyRes: (proxyRes, req, res) => {
        let body = [];
        proxyRes.on('data', (chunk) => body.push(chunk));
        proxyRes.on('end', () => {
          res.status(proxyRes.statusCode);
          Object.keys(proxyRes.headers).forEach(key => {
            res.setHeader(key, proxyRes.headers[key]);
          });
          res.send(Buffer.concat(body));
          resolve(true);
        });
      },
      selfHandleResponse: true
    });
    proxy(req, res, () => {});
  });
}

app.use('*', async (req, res, next) => {
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
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws, req) => {
  logger.info('WebSocket connection established');

  const primary = getPrimaryBackend(req.url);
  const wsUrl = primary.url.replace('http:', 'ws:').replace('https:', 'wss:');

  const backendWs = new WebSocket(wsUrl);

  backendWs.on('open', () => {
    ws.on('message', (data) => backendWs.send(data));
    backendWs.on('message', (data) => ws.send(data));
  });

  backendWs.on('error', (err) => {
    logger.error(`WebSocket error: ${err.message}`);
    ws.close();
  });

  ws.on('close', () => backendWs.close());
});

server.listen(PORT, () => {
  logger.info(`Middleware running on port ${PORT}`);
  logger.info(`Primary: JavaScript (${config.backends.javascript.url})`);
  logger.info(`Fallback: Python (${config.backends.python.url})`);
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
process.on('SIGINT', () => server.close(() => process.exit(0)));
