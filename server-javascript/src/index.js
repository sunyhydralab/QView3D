import express from 'express';
import http from 'http';
import cors from 'cors';
import compression from 'compression';
import { SerialPort } from './serialport.js';
import { Printer } from './printer.js';
import database from './database.js';
import wsManager from './websocket.js';
import jobsRouter from './routes/jobs.js';
import fabricatorsRouter from './routes/fabricators.js';
import issuesRouter from './routes/issues.js';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

// Store active printers
const activePrinters = new Map();

// Initialize database
database.init()
  .then(() => console.log('Database initialized'))
  .catch(err => {
    console.error('Failed to initialize database:', err);
    process.exit(1);
  });

// Middleware
app.use(cors());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
  next();
});

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'qview3d-javascript-backend',
    uptime: process.uptime()
  });
});

// Register route handlers
app.use('/', jobsRouter);
app.use('/', fabricatorsRouter);
app.use('/', issuesRouter);

// Serial port direct access routes
app.get('/api/serial/ports', async (req, res) => {
  try {
    const ports = await SerialPort.list();
    res.json(ports.map(port => ({
      path: port.path,
      manufacturer: port.manufacturer || '',
      serialNumber: port.serialNumber || '',
      available: true
    })));
  } catch (error) {
    res.status(500).json({
      error: 'Failed to list serial ports',
      details: error.message
    });
  }
});

app.post('/api/serial/connect', (req, res) => {
  try {
    const { port, baudRate = 115200 } = req.body;

    if (!port) {
      return res.status(400).json({ error: 'Port is required' });
    }

    const printer = new Printer();

    printer.setSerialPort(port, () => {
      activePrinters.set(port, printer);
      res.json({
        success: true,
        message: `Connected to printer on ${port}`,
        port,
        state: printer.getCurrentState()
      });
    }, baudRate);

  } catch (error) {
    res.status(500).json({
      error: 'Failed to connect to printer',
      details: error.message
    });
  }
});

app.post('/api/serial/send', (req, res) => {
  try {
    const { port, command } = req.body;

    if (!port || !command) {
      return res.status(400).json({ error: 'Port and command are required' });
    }

    const printer = activePrinters.get(port);

    if (!printer) {
      return res.status(404).json({ error: 'No active printer on this port' });
    }

    printer._sendGcodeCommand(command + '\n');

    res.json({
      success: true,
      message: 'Command sent',
      command
    });

  } catch (error) {
    res.status(500).json({
      error: 'Failed to send command',
      details: error.message
    });
  }
});

app.get('/api/printers', (req, res) => {
  const printers = Array.from(activePrinters.entries()).map(([port, printer]) => ({
    port,
    state: printer.getCurrentState()
  }));

  res.json(printers);
});

app.post('/api/serial/disconnect', (req, res) => {
  try {
    const { port } = req.body;

    if (!port) {
      return res.status(400).json({ error: 'Port is required' });
    }

    const printer = activePrinters.get(port);

    if (!printer) {
      return res.status(404).json({ error: 'No active printer on this port' });
    }

    printer.closeSerialPort();
    activePrinters.delete(port);

    res.json({
      success: true,
      message: `Disconnected from printer on ${port}`
    });

  } catch (error) {
    res.status(500).json({
      error: 'Failed to disconnect',
      details: error.message
    });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({
    error: 'Internal server error',
    details: err.message
  });
});

// Initialize WebSocket
wsManager.initialize(server);

// Start server
server.listen(PORT, () => {
  console.log(`QView3D JavaScript backend listening on port ${PORT}`);
  console.log(`WebSocket server available on same port`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  wsManager.close();
  database.close().then(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  wsManager.close();
  database.close().then(() => process.exit(0));
});
