/**
 * QView3D Middleware Server
 *
 * This middleware server acts as a reverse proxy between the frontend and backend services.
 * It proxies to the Vite dev server for dynamic frontend development and provides
 * intelligent routing based on the route map configuration.
 *
 * Architecture:
 * Browser (8002) → Middleware (8002) → Vite Dev Server (5173) / Backend (8000 Python / 8005 JavaScript)
 * - Frontend: Proxied to Vite dev server on port 5173
 * - API Routes: Proxied to backend based on route mapping
 */

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { io as ioClient } from 'socket.io-client';
import path from 'path';
import { fileURLToPath } from 'url';
import config from './config/backends.js';
import { routeMap, defaultBackend } from './config/routes.js';
import { HealthChecker } from './healthCheck.js';

// Get __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = config.middleware.port || 8002;

// Current selected backend (defaults to config)
let selectedBackend = config.middleware.mode || 'python';

// Initialize health checker
const healthChecker = new HealthChecker(config.backends, 10000);

// Middleware setup
app.use(cors({
  origin: '*',
  credentials: true
}));

// REMOVED: app.use(express.json());
// Let the proxy forward raw request bodies to the backend
// The backend will parse the JSON, not the middleware

/**
 * Get the active backend configuration
 */
function getActiveBackend() {
  return selectedBackend === 'python' ? config.backends.python : config.backends.javascript;
}

/**
 * Get backend for a specific route based on route mapping
 * @param {string} path - The request path
 * @returns {Object} Backend configuration object for the route
 */
function getBackendForRoute(path) {
  // Check if route is explicitly mapped
  const mappedBackend = routeMap[path];

  if (mappedBackend === 'python') {
    return config.backends.python;
  } else if (mappedBackend === 'javascript') {
    return config.backends.javascript;
  } else if (mappedBackend === 'either') {
    // For 'either' routes, use the currently selected backend
    return getActiveBackend();
  }

  // If no explicit mapping, use default backend
  return defaultBackend === 'python' ? config.backends.python : config.backends.javascript;
}

/**
 * Health check endpoint
 * Shows middleware and backend health status
 */
app.get('/api/middleware/health', async (req, res) => {
  const { debug } = req.query;

  if (debug === 'true') {
    // Debug mode: show full backend status
    const backendStatus = healthChecker.getAllStatus();

    res.json({
      status: 'healthy',
      middleware: {
        uptime: process.uptime(),
        selectedBackend: selectedBackend,
        monitoringInterval: healthChecker.interval
      },
      backends: backendStatus
    });
  } else {
    // No debug mode: minimal response with backend status
    const backendStatus = healthChecker.getAllStatus();

    res.json({
      status: 'healthy',
      backends: Object.keys(backendStatus).reduce((acc, name) => {
        acc[name] = {
          status: backendStatus[name].status,
          responseTime: backendStatus[name].responseTime
        };
        return acc;
      }, {})
    });
  }
});

/**
 * API routes that should be proxied to the backend
 */
const apiRoutes = [
  '/api',
  '/socket.io',
  '/getfabricators',
  '/registerfabricator',
  '/deletefabricator',
  '/pauseprinter',
  '/resumeprinter',
  '/cancelprinter',
  '/getqueue',
  '/reorderqueue',
  '/clearqueue',
  '/uploadfiles',
  '/getfiles',
  '/deletefile',
  '/addjob',
  '/canceljob',
  '/getjobhistory',
  '/getjobs',  // Added - frontend calls this
  '/getports',  // Added - frontend calls this
  '/register',  // Added - frontend calls this
  '/setstatus',  // Added - frontend calls this
  '/startprint',  // Added - frontend calls this
  '/releasejob',  // Added - frontend calls this
  '/autoqueue',  // Added - frontend calls this
  '/cancelfromqueue',  // Added - frontend calls this
  '/addjobtoqueue',  // Added - frontend calls this
  '/startemulator',
  '/registeremulator',
  '/disconnectemulator',
  '/getissues',
  '/createissue',
  '/updateissue',
  '/deleteissue',
  '/resolveissue',
  '/health',
  '/getprinterinfo',
  '/serverVersion'
];

/**
 * Apply proxy middleware ONLY to specific API routes
 */
apiRoutes.forEach(route => {
  app.use(route, createProxyMiddleware({
    router: (req) => {
      // Build full path for route determination
      let fullPath = req.baseUrl;
      if (req.url !== '/') {
        fullPath += req.url;
      }
      // Use getBackendForRoute to determine the appropriate backend
      const backend = getBackendForRoute(fullPath);
      return backend.url;
    },
    changeOrigin: true,
    ws: route === '/socket.io',  // Enable WebSocket for Socket.IO
    // Strip /api prefix when forwarding to backend (backend routes don't have /api prefix)
    pathRewrite: (path, req) => {
      // The original route is in req.baseUrl, and the remaining path is in req.url
      // If req.url is just '/', we want just the baseUrl without the trailing slash
      let fullPath = req.baseUrl;
      if (req.url !== '/') {
        fullPath += req.url;
      }
      const backend = getBackendForRoute(fullPath);

      // Check backend health and warn if unhealthy
      const backendName = backend.url.includes(':8000') ? 'python' : 'javascript';
      const backendHealth = healthChecker.getStatus(backendName);

      if (backendHealth && backendHealth.status !== 'healthy') {
        console.warn(`[Proxy] WARNING: Routing to ${backendHealth.status} backend (${backendName}): ${fullPath}`);
      }

      // Strip /api prefix for backend routes
      // Backend routes are defined without /api prefix (e.g., /createissue, /emulator/list)
      let rewrittenPath = fullPath;
      if (fullPath.startsWith('/api/')) {
        rewrittenPath = fullPath.substring(4); // Remove '/api' prefix
      }

      console.log(`[Proxy] ${req.method} ${fullPath} → ${backend.url}${rewrittenPath}`);
      return rewrittenPath;
    },
    onError: (err, req, res) => {
      console.error(`[Proxy Error] ${req.path}:`, err.message);
      if (res.headersSent) return;
      // Build full path for error handling
      let fullPath = req.baseUrl;
      if (req.url !== '/') {
        fullPath += req.url;
      }
      const backend = getBackendForRoute(fullPath);
      res.status(500).json({
        error: 'Backend connection failed',
        message: err.message,
        backend: backend.url
      });
    }
  }));
});

/**
 * Proxy to Vite dev server for dynamic frontend development
 * IMPORTANT: This must come AFTER API proxies to avoid intercepting API routes
 */
const VITE_DEV_SERVER = 'http://localhost:5173';

app.use('/', createProxyMiddleware({
  target: VITE_DEV_SERVER,
  changeOrigin: true,
  ws: true,  // Enable WebSocket for Vite HMR
  onError: (err, req, res) => {
    console.error(`[Vite Proxy Error] ${req.path}:`, err.message);
    if (res.headersSent) return;
    res.status(502).json({
      error: 'Vite dev server connection failed',
      message: err.message,
      hint: 'Make sure Vite dev server is running on port 5173'
    });
  },
  onProxyReq: (proxyReq, req, res) => {
    // Log proxied requests to Vite (only non-asset requests to reduce noise)
    if (!req.path.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
      console.log(`[Vite Proxy] ${req.method} ${req.path} → ${VITE_DEV_SERVER}${req.path}`);
    }
  }
}));

/**
 * Create HTTP server and Socket.IO server
 */
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  },
  transports: ['websocket', 'polling']
});

// Socket.IO proxy to backend
let backendSocket = null;

function connectToBackend() {
  const backend = getActiveBackend();
  const backendUrl = backend.url;

  console.log(`[SocketIO] Connecting to backend at ${backendUrl}`);

  // Disconnect existing connection if any
  if (backendSocket) {
    backendSocket.disconnect();
  }

  // Connect to backend SocketIO
  backendSocket = ioClient(backendUrl, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 10
  });

  backendSocket.on('connect', () => {
    console.log(`✓ Connected to backend SocketIO at ${backendUrl}`);
  });

  backendSocket.on('disconnect', () => {
    console.log(`✗ Disconnected from backend SocketIO`);
  });

  backendSocket.on('connect_error', (error) => {
    console.error(`[SocketIO Error] Failed to connect to backend:`, error.message);
  });

  // Forward all backend events to frontend clients
  backendSocket.onAny((event, ...args) => {
    console.log(`[SocketIO] Backend → Clients: ${event}`);
    io.emit(event, ...args);
  });
}

// Handle frontend client connections
io.on('connection', (socket) => {
  console.log(`[SocketIO] Client connected: ${socket.id}`);

  // Connect to backend if not already connected
  if (!backendSocket || !backendSocket.connected) {
    connectToBackend();
  }

  // Forward all client events to backend
  socket.onAny((event, ...args) => {
    console.log(`[SocketIO] Client → Backend: ${event}`);
    if (backendSocket && backendSocket.connected) {
      backendSocket.emit(event, ...args);
    } else {
      console.warn(`[SocketIO] Backend not connected, cannot forward event: ${event}`);
      socket.emit('error', { message: 'Backend connection not available' });
    }
  });

  socket.on('disconnect', () => {
    console.log(`[SocketIO] Client disconnected: ${socket.id}`);
  });
});

// Start server
server.listen(PORT, () => {
  console.log('\n' + '='.repeat(80));
  console.log('QView3D - MIDDLEWARE SERVER READY');
  console.log('='.repeat(80));
  console.log('');
  console.log(`  🌐 ACCESS APPLICATION AT:  http://localhost:${PORT}`);
  console.log('');
  console.log(`  Architecture:`);
  console.log(`    Browser → Middleware (${PORT}) → Backend (${getActiveBackend().url})`);
  console.log('');
  console.log(`  Middleware Functions:`);
  console.log(`    - Proxying Frontend: Vite dev server (http://localhost:5173)`);
  console.log(`    - Proxying ${apiRoutes.length} API routes to backend`);
  console.log(`    - Handling WebSocket connections`);
  console.log(`    - Monitoring backend health every 10s`);
  console.log('');
  console.log(`  Active Backend:  ${selectedBackend}`);
  console.log(`  Backend URL:     ${getActiveBackend().url}`);
  console.log('');
  console.log('='.repeat(80));
  console.log('');

  // Start health monitoring
  healthChecker.start();

  // Connect to backend SocketIO
  connectToBackend();
});
