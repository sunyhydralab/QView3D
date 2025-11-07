/**
 * QView3D Middleware Server
 *
 * This middleware server acts as a reverse proxy between the frontend and backend services.
 * It proxies to the Vite dev server for dynamic frontend development and routes all API
 * requests to a single backend selected at startup.
 *
 * Architecture:
 * Browser (8002) → Middleware (8002) → Vite Dev Server (5173) / Backend (8000 Python / 8005 JavaScript)
 * - Frontend: Proxied to Vite dev server on port 5173
 * - API Routes: Statically routed to backend selected at startup
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
import { HealthChecker } from './healthCheck.js';

// Get __dirname in ES modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = config.middleware.port || 8002;

// Debug logging flag (set to true for verbose output)
const DEBUG = process.env.DEBUG === 'true' || false;

// Backend selection - determined once at startup from config
const SELECTED_BACKEND = config.middleware.mode || 'python';
const BACKEND_CONFIG = SELECTED_BACKEND === 'python' ? config.backends.python : config.backends.javascript;
const BACKEND_TARGET_URL = BACKEND_CONFIG.url;
const BACKEND_NAME = SELECTED_BACKEND;

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
        selectedBackend: SELECTED_BACKEND,
        targetUrl: BACKEND_TARGET_URL,
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
 * Routes are organized by HTTP method they should accept
 */
const apiRoutes = {
  // Routes that accept both GET and POST (or other methods)
  all: [
    '/api',
    '/socket.io',
    '/getfabricators',
    '/getports',
    '/getqueue',
    '/getjobhistory',
    '/getjobs',
    '/getfiles',
    '/getfile',  // Added for fetching individual GCode files
    '/getissues',
    '/getprinterinfo',
    '/health',
    '/serverVersion'
  ],
  // Routes that only accept POST (should not intercept GET for SPA routing)
  postOnly: [
    '/register',
    '/registerfabricator',
    '/deletefabricator',
    '/pauseprinter',
    '/resumeprinter',
    '/cancelprinter',
    '/reorderqueue',
    '/clearqueue',
    '/uploadfiles',
    '/deletefile',
    '/addjob',
    '/canceljob',
    '/setstatus',
    '/startprint',
    '/releasejob',
    '/autoqueue',
    '/cancelfromqueue',
    '/addjobtoqueue',
    '/startemulator',
    '/registeremulator',
    '/disconnectemulator',
    '/createissue',
    '/updateissue',
    '/deleteissue',
    '/resolveissue'
  ]
};

// Helper function to create proxy middleware
const createProxy = (route) => createProxyMiddleware({
  target: BACKEND_TARGET_URL,
  changeOrigin: true,
  ws: route === '/socket.io',
  pathRewrite: (path, req) => {
    let fullPath = req.baseUrl;
    if (req.url !== '/') {
      fullPath += req.url;
    }

    const backendHealth = healthChecker.getStatus(BACKEND_NAME);
    if (backendHealth && backendHealth.status !== 'healthy') {
      console.warn(`[Proxy] WARNING: Routing to ${backendHealth.status} backend (${BACKEND_NAME}): ${fullPath}`);
    }

    let rewrittenPath = fullPath;
    if (fullPath.startsWith('/api/')) {
      rewrittenPath = fullPath.substring(4);
    }

    if (DEBUG) {
      console.log(`[Proxy] ${req.method} ${fullPath} → ${BACKEND_TARGET_URL}${rewrittenPath}`);
    }
    return rewrittenPath;
  },
  onError: (err, req, res) => {
    console.error(`[Proxy Error] ${req.path}:`, err.message);
    if (res.headersSent) return;
    res.status(500).json({
      error: 'Backend connection failed',
      message: err.message,
      backend: BACKEND_TARGET_URL
    });
  }
});

/**
 * Apply proxy middleware to API routes
 * POST-only routes only proxy POST requests to allow SPA routing for GET
 */
apiRoutes.all.forEach(route => {
  app.use(route, createProxy(route));
});

// POST-only routes: only proxy POST requests, let GET fall through to Vite
apiRoutes.postOnly.forEach(route => {
  app.post(route, createProxy(route));
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
    // Log proxied requests to Vite in debug mode only
    if (DEBUG && !req.path.match(/\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$/)) {
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
  if (DEBUG) console.log(`[SocketIO] Connecting to backend at ${BACKEND_TARGET_URL}`);

  // Disconnect existing connection if any
  if (backendSocket) {
    backendSocket.disconnect();
  }

  // Connect to backend SocketIO
  backendSocket = ioClient(BACKEND_TARGET_URL, {
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: 10
  });

  backendSocket.on('connect', () => {
    if (DEBUG) console.log(`Connected to backend SocketIO at ${BACKEND_TARGET_URL}`);
  });

  backendSocket.on('disconnect', () => {
    if (DEBUG) console.log(`Disconnected from backend SocketIO`);
  });

  backendSocket.on('connect_error', (error) => {
    console.error(`[SocketIO Error] Failed to connect to backend:`, error.message);
  });

  // Forward all backend events to frontend clients
  backendSocket.onAny((event, ...args) => {
    if (DEBUG) console.log(`[SocketIO] Backend → Clients: ${event}`);
    io.emit(event, ...args);
  });
}

// Handle frontend client connections
io.on('connection', (socket) => {
  if (DEBUG) console.log(`[SocketIO] Client connected: ${socket.id}`);

  // Connect to backend if not already connected
  if (!backendSocket || !backendSocket.connected) {
    connectToBackend();
  }

  // Forward all client events to backend
  socket.onAny((event, ...args) => {
    if (DEBUG) console.log(`[SocketIO] Client → Backend: ${event}`);
    if (backendSocket && backendSocket.connected) {
      backendSocket.emit(event, ...args);
    } else {
      console.warn(`[SocketIO] Backend not connected, cannot forward event: ${event}`);
      socket.emit('error', { message: 'Backend connection not available' });
    }
  });

  socket.on('disconnect', () => {
    if (DEBUG) console.log(`[SocketIO] Client disconnected: ${socket.id}`);
  });
});

// Start server
server.listen(PORT, () => {
  console.log('\n' + '='.repeat(80));
  console.log('QView3D - MIDDLEWARE SERVER READY');
  console.log('='.repeat(80));
  console.log('');
  console.log(`  ACCESS APPLICATION AT:  http://localhost:${PORT}`);
  console.log('');
  console.log(`  Architecture:`);
  console.log(`    Browser → Middleware (${PORT}) → Backend (${BACKEND_TARGET_URL})`);
  console.log('');
  console.log(`  Middleware Functions:`);
  console.log(`    - Proxying Frontend: Vite dev server (http://localhost:5173)`);
  console.log(`    - Proxying ${apiRoutes.all.length + apiRoutes.postOnly.length} API routes to backend (static routing)`);
  console.log(`    - Handling WebSocket connections`);
  console.log(`    - Monitoring backend health every 10s`);
  console.log('');
  console.log(`  Active Backend:  ${SELECTED_BACKEND}`);
  console.log(`  Backend URL:     ${BACKEND_TARGET_URL}`);
  console.log('');
  console.log('='.repeat(80));
  console.log('');

  // Start health monitoring
  healthChecker.start();

  // Connect to backend SocketIO
  connectToBackend();
});
