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
import emulatorRouter from './routes/emulator.js';
import hardwareRouter from './routes/hardware.js';
import fabricatorManager from './fabricatorManager.js';

const app = express();
const server = http.createServer(app);
const PORT = process.env.PORT || 3000;

// Store active printers
const activePrinters = new Map();

// Generate random string for mock serial
function generateMockSerial() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Create default emulator if none exist
async function createDefaultEmulator() {
  try {
    // Check if any EMU_ printers exist in database
    const existingEmulators = await database.all('SELECT id FROM fabricators WHERE devicePort LIKE "EMU_%"');

    if (existingEmulators && existingEmulators.length > 0) {
      console.log(`Found ${existingEmulators.length} existing emulator(s), skipping default creation`);
      return;
    }

    // No emulators exist, create default one
    const printerName = 'Test Printer';
    const mockSerial = generateMockSerial();
    const portPath = `EMU_${mockSerial}`;

    // Get max position for ordering
    const maxPos = await database.get('SELECT MAX(position) as max_pos FROM fabricators');
    const position = (maxPos?.max_pos || 0) + 1;

    // Create mock printer in database
    const result = await database.run(
      'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
      [printerName, portPath, position, 'ready']
    );

    console.log(`Default emulator created: ${printerName} on ${portPath} (ID: ${result.id})`);

    // Broadcast to frontend
    wsManager.broadcast({
      event: 'fabricator_added',
      data: {
        id: result.id,
        name: printerName,
        devicePort: portPath,
        status: 'ready'
      }
    });
  } catch (error) {
    // Don't crash if creation fails, just log the error
    console.error('Failed to create default emulator (non-fatal):', error.message);
  }
}

// Initialize database and fabricator manager
database.init()
  .then(() => {
    console.log('Database initialized');
    return fabricatorManager.initialize();
  })
  .then(() => {
    console.log('FabricatorManager initialized');
    return createDefaultEmulator();
  })
  .catch(err => {
    console.error('Failed to initialize:', err);
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

// Server version endpoint - returns version from package.json or environment variable
app.get('/serverVersion', (req, res) => {
  try {
    // Check environment variable first (matches Python behavior)
    const version = process.env.SERVER_VERSION || process.env.VERSION || '0.0.1';

    // Return simple string response to match Python endpoint behavior
    res.json(version);
  } catch (error) {
    console.error('Error getting server version:', error);
    res.status(500).json({ error: 'Failed to get server version' });
  }
});

// Get printer info endpoint - returns all fabricators with full status information
// Matches Python's /getprinterinfo endpoint which returns fabricator.__to_JSON__() for all fabricators
app.get('/getprinterinfo', async (req, res) => {
  try {
    // Get all fabricators from database
    const fabricators = await database.all('SELECT * FROM fabricators ORDER BY position ASC');

    // Build full fabricator info with queue and job details
    const printerInfo = await Promise.all(
      fabricators.map(async (fabricator) => {
        // Get the queue for this fabricator
        const queue = fabricatorManager.getQueue(fabricator.id);
        const queueData = queue ? queue.toJSON() : [];

        // Get current job (first item in queue)
        const currentJob = queueData.length > 0 ? queueData[0] : null;

        // Get full job details if there's a current job
        let jobDetails = null;
        if (currentJob) {
          jobDetails = await database.get('SELECT * FROM jobs WHERE id = ?', [currentJob.id]);
        }

        // Build fabricator JSON response matching Python's Fabricator.__to_JSON__() format
        return {
          id: fabricator.id,
          name: fabricator.name,
          description: fabricator.model || 'Unknown Model',
          hwid: fabricator.hwid || '',
          status: fabricator.status || 'offline',
          date: fabricator.created_at || new Date().toISOString(),
          queue: queueData,
          job: jobDetails,
          device: {
            // Basic device info - extended device details would come from serial connection
            serialPort: fabricator.devicePort,
            model: fabricator.model,
            status: fabricator.status,
            // Additional device properties can be added as needed
            homePosition: null,
            temperatures: {
              bed: 0,
              extruder: 0
            },
            position: {
              x: 0,
              y: 0,
              z: 0
            }
          },
          consoles: [[], [], [], [], []] // Match Python's console structure
        };
      })
    );

    res.json(printerInfo);
  } catch (error) {
    console.error('Error getting printer info:', error);
    res.status(500).json({
      error: 'Failed to get printer info',
      details: error.message
    });
  }
});

// Register route handlers
app.use('/', jobsRouter);
app.use('/', fabricatorsRouter);
app.use('/', issuesRouter);
app.use('/', emulatorRouter);
app.use('/', hardwareRouter);

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
  fabricatorManager.stopProcessor();
  wsManager.close();
  database.close().then(() => process.exit(0));
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  fabricatorManager.stopProcessor();
  wsManager.close();
  database.close().then(() => process.exit(0));
});
