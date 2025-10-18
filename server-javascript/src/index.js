import express from 'express';
import { SerialPort } from './serialport.js';
import { Printer } from './printer.js';
import cors from 'cors';

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Store active printers
const activePrinters = new Map();

// Health endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'qview3d-javascript-backend'
  });
});

// Get available serial ports
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

// Connect to a printer
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

// Send G-code command
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

    // Send raw command
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

// Get printer status
app.get('/api/printers', (req, res) => {
  const printers = Array.from(activePrinters.entries()).map(([port, printer]) => ({
    port,
    state: printer.getCurrentState()
  }));

  res.json(printers);
});

// Disconnect printer
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

app.listen(PORT, () => {
  console.log(`QView3D JavaScript backend listening on port ${PORT}`);
});
