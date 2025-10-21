/**
 * QView3D Middleware Server
 *
 * This middleware server acts as a reverse proxy between the frontend and backend services.
 * It provides intelligent routing based on the route map configuration.
 *
 * Architecture:
 * Browser (8002) → Middleware (8002) → Backend (8000 Python / 8005 JavaScript)
 */

import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import cors from 'cors';
import { createServer } from 'http';
import { Server } from 'socket.io';
import { io as ioClient } from 'socket.io-client';
import config from './config/backends.js';
import { routeMap, defaultBackend } from './config/routes.js';

const app = express();
const PORT = config.middleware.port || 8002;

// Current selected backend (defaults to config)
let selectedBackend = config.middleware.mode || 'python';

// Middleware setup
app.use(cors({
  origin: '*',
  credentials: true
}));

app.use(express.json());

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
 */
app.get('/api/middleware/health', (req, res) => {
  res.json({
    status: 'healthy',
    middleware_port: PORT,
    active_backend: selectedBackend,
    backend_url: getActiveBackend().url
  });
});

/**
 * Backend selection endpoint
 */
app.post('/api/middleware/select-backend', (req, res) => {
  const { backend } = req.body;
  if (backend === 'python' || backend === 'javascript') {
    selectedBackend = backend;
    console.log(`✓ Switched to ${backend} backend`);
    res.json({
      success: true,
      active_backend: selectedBackend,
      backend_url: getActiveBackend().url
    });
  } else {
    res.status(400).json({
      success: false,
      error: 'Invalid backend. Must be "python" or "javascript"'
    });
  }
});


/**
 * Proxy all routes to backend
 * Middleware is ONLY for proxying - backend serves the frontend
 */
app.use('/', createProxyMiddleware({
  target: getActiveBackend().url,
  changeOrigin: true,
  ws: false,  // WebSocket handled separately below
  router: (req) => {
    // Determine target based on the specific route
    const backend = getBackendForRoute(req.path);
    console.log(`[Proxy] ${req.method} ${req.path} → ${backend.url}`);
    return backend.url;
  },
  onError: (err, req, res) => {
    console.error(`[Proxy Error] ${req.path}:`, err.message);
    if (res.headersSent) return;
    res.status(500).json({
      error: 'Backend connection failed',
      message: err.message,
      backend: getActiveBackend().url
    });
  },
  onProxyReq: (proxyReq, req, res) => {
    // Log proxy requests for debugging
    console.log(`  → Proxying to: ${proxyReq.host}${proxyReq.path}`);
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
  console.log('\n' + '='.repeat(60));
  console.log('QView3D Middleware Server');
  console.log('='.repeat(60));
  console.log(`Middleware:     http://localhost:${PORT}`);
  console.log(`Active Backend: ${selectedBackend} (${getActiveBackend().url})`);
  console.log('='.repeat(60));
  console.log('Ready to proxy requests to backend\n');

  // Connect to backend SocketIO
  connectToBackend();
});

// Handle backend switching
export function switchBackend(backend) {
  if (backend === 'python' || backend === 'javascript') {
    selectedBackend = backend;
    connectToBackend();
    return true;
  }
  return false;
}

// Export for external use
export { getActiveBackend, getBackendForRoute, selectedBackend };
