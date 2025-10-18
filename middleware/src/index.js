import express from 'express';
import cors from 'cors';
import { createProxyMiddleware } from 'http-proxy-middleware';
import WebSocket from 'ws';
import http from 'http';

import config from './config/backends.js';
import { BackendSelector } from './services/backendSelector.js';
import { ResponseNormalizer } from './services/responseNormalizer.js';
import { HealthMonitor } from './services/healthMonitor.js';
import { WebSocketProxy } from './websocket/wsProxy.js';
import logger from './utils/logger.js';
import { handleError } from './utils/errorHandler.js';

const app = express();
const PORT = config.middleware.port;

// Initialize services
const healthMonitor = new HealthMonitor(config.backends);
const backendSelector = new BackendSelector(
  config.backends,
  config.routingMode,
  healthMonitor
);
const normalizer = new ResponseNormalizer();
const wsProxy = new WebSocketProxy(config.backends, config.routingMode);

// Middleware
app.use(cors(config.corsOptions));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  const start = Date.now();
  logger.logRequest(req);

  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.logResponse(res, duration);
  });

  next();
});

// Health check endpoint
app.get('/health', (req, res) => {
  const health = {
    middleware: 'healthy',
    mode: config.routingMode,
    backends: healthMonitor.getStatus(),
    uptime: process.uptime()
  };
  res.json(health);
});

// Dynamic proxy for all routes
app.use('*', (req, res, next) => {
  const backend = backendSelector.selectBackend(req);

  if (!backend) {
    return res.status(503).json({
      error: 'No backend available',
      mode: config.routingMode
    });
  }

  // Create proxy middleware
  const proxy = createProxyMiddleware({
    target: backend.url,
    changeOrigin: true,
    onError: (err, req, res) => {
      logger.error(`Proxy error for ${req.path}: ${err.message}`);

      // Try fallback in hybrid mode
      if (config.routingMode === 'hybrid') {
        const alternate = backendSelector.getAlternateBackend('python');
        if (alternate && healthMonitor.isBackendHealthy(alternate.name)) {
          logger.info(`Retrying with ${alternate.name} backend`);
          // Note: In production, implement retry logic here
        }
      }

      res.status(502).json({
        error: 'Backend unavailable',
        details: err.message
      });
    },
    onProxyRes: (proxyRes, req, res) => {
      // Collect response data
      let body = [];
      proxyRes.on('data', (chunk) => {
        body.push(chunk);
      });

      proxyRes.on('end', () => {
        const bodyStr = Buffer.concat(body).toString();

        // Try to normalize if JSON
        try {
          const data = JSON.parse(bodyStr);
          const normalized = normalizer.normalize(
            data,
            backend === config.backends.python ? 'python' : 'javascript',
            req.path
          );

          // Send normalized response
          res.status(proxyRes.statusCode);
          Object.keys(proxyRes.headers).forEach(key => {
            res.setHeader(key, proxyRes.headers[key]);
          });
          res.json(normalized);
        } catch (e) {
          // Not JSON or parse error, send as-is
          res.status(proxyRes.statusCode);
          Object.keys(proxyRes.headers).forEach(key => {
            res.setHeader(key, proxyRes.headers[key]);
          });
          res.send(bodyStr);
        }
      });
    },
    selfHandleResponse: true  // We handle the response ourselves
  });

  proxy(req, res, next);
});

// Error handler
app.use(handleError);

// Create HTTP server
const server = http.createServer(app);

// WebSocket server
const wss = new WebSocket.Server({ server });

wss.on('connection', (ws, req) => {
  wsProxy.handleConnection(ws, req);
});

// Start health monitoring
healthMonitor.startMonitoring();

// Start server
server.listen(PORT, () => {
  logger.info(`QView3D Middleware running on port ${PORT}`);
  logger.info(`Mode: ${config.routingMode}`);
  logger.info(`Python backend: ${config.backends.python.url}`);
  logger.info(`JavaScript backend: ${config.backends.javascript.url}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  healthMonitor.stopMonitoring();
  wsProxy.close();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  healthMonitor.stopMonitoring();
  wsProxy.close();
  server.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});
