import express from 'express';
import database from '../database.js';
import virtualSerialManager, { VirtualSerialPort } from '../virtualSerial.js';
import wsManager from '../websocket.js';
import fabricatorManager from '../fabricatorManager.js';

const router = express.Router();

// Store active emulator instances
const activeEmulators = new Map();

// Start emulator
router.post('/startemulator', async (req, res) => {
  try {
    const { model, config } = req.body;

    // Create virtual serial port
    const portPath = virtualSerialManager.createPort(config?.port || null);
    const virtualPort = virtualSerialManager.getPort(portPath);

    // Open the virtual port
    virtualPort.open((err) => {
      if (err) {
        console.error('Error opening virtual port:', err);
        return res.status(500).json({ error: 'Failed to open virtual port' });
      }

      // Store emulator info
      activeEmulators.set(portPath, {
        model,
        config: {
          ...config,
          port: portPath
        },
        virtualPort,
        started: new Date()
      });

      // Broadcast status update
      wsManager.broadcast({
        event: 'emulator_status',
        data: {
          status: 'Connected',
          message: `Emulator started on ${portPath}`
        }
      });

      console.log(`Emulator started: ${model} on ${portPath}`);

      res.json({
        success: true,
        message: 'Emulator started successfully',
        port: portPath,
        model
      });
    });
  } catch (error) {
    console.error('Error starting emulator:', error);
    res.status(500).json({ error: 'Failed to start emulator', details: error.message });
  }
});

// Disconnect emulator
router.post('/disconnectemulator', async (req, res) => {
  try {
    const { printerConfig } = req.body;
    const portPath = printerConfig?.port;

    if (!portPath) {
      return res.status(400).json({ error: 'No port specified' });
    }

    const emulator = activeEmulators.get(portPath);

    if (!emulator) {
      return res.status(404).json({ error: 'Emulator not found' });
    }

    // Close virtual port
    if (emulator.virtualPort) {
      emulator.virtualPort.close();
    }

    // Delete virtual port
    virtualSerialManager.deletePort(portPath);

    // Remove from active emulators
    activeEmulators.delete(portPath);

    // Try to remove from database if it was registered
    const fabricator = await database.get('SELECT id FROM fabricators WHERE devicePort = ?', [portPath]);
    if (fabricator) {
      await database.run('DELETE FROM fabricators WHERE id = ?', [fabricator.id]);
      fabricatorManager.removeQueue(fabricator.id);
    }

    // Broadcast status update
    wsManager.broadcast({
      event: 'emulator_status',
      data: {
        status: 'Offline',
        message: 'Emulator disconnected'
      }
    });

    res.json({
      success: true,
      message: 'Emulator disconnected successfully'
    });
  } catch (error) {
    console.error('Error disconnecting emulator:', error);
    res.status(500).json({ error: 'Failed to disconnect emulator', details: error.message });
  }
});

// Register emulator as a fabricator
router.post('/registeremulator', async (req, res) => {
  try {
    const { model, config } = req.body;
    const portPath = config?.port;

    if (!portPath) {
      return res.status(400).json({ error: 'No port specified' });
    }

    const emulator = activeEmulators.get(portPath);

    if (!emulator) {
      return res.status(404).json({ error: 'Emulator not found. Please start the emulator first.' });
    }

    // Check if already registered
    const existing = await database.get('SELECT id FROM fabricators WHERE devicePort = ?', [portPath]);

    if (existing) {
      return res.json({
        success: true,
        message: 'Emulator already registered',
        fabricator_id: existing.id
      });
    }

    // Get max position
    const maxPos = await database.get('SELECT MAX(position) as max_pos FROM fabricators');
    const position = (maxPos?.max_pos || 0) + 1;

    // Register as fabricator
    const result = await database.run(
      'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
      [config.name || 'Emulator Printer', portPath, position, 'ready']
    );

    // Create queue for the emulator
    fabricatorManager.createQueue(result.id);

    // Broadcast registration success
    wsManager.broadcast({
      event: 'emulator_registered',
      data: {
        name: config.name || 'Emulator Printer',
        id: result.id
      }
    });

    wsManager.broadcast({
      event: 'fabricator_added',
      data: {
        id: result.id,
        name: config.name || 'Emulator Printer',
        devicePort: portPath,
        status: 'ready'
      }
    });

    console.log(`Emulator registered as fabricator ID: ${result.id}`);

    res.json({
      success: true,
      message: 'Emulator registered successfully',
      fabricator_id: result.id
    });
  } catch (error) {
    console.error('Error registering emulator:', error);
    res.status(500).json({ error: 'Failed to register emulator', details: error.message });
  }
});

// Set emulator temperature
router.post('/setemulatortemperature', async (req, res) => {
  try {
    const { extruder, bed, port } = req.body;

    // Find the emulator port
    let emulator = null;
    let emulatorPort = null;

    if (port) {
      emulator = activeEmulators.get(port);
      emulatorPort = port;
    } else {
      // Find first active emulator
      for (const [path, emu] of activeEmulators.entries()) {
        emulator = emu;
        emulatorPort = path;
        break;
      }
    }

    if (!emulator) {
      return res.status(404).json({ error: 'No active emulator found' });
    }

    const virtualPort = emulator.virtualPort;

    if (extruder !== undefined) {
      virtualPort.write(`M104 S${extruder}\n`);
    }

    if (bed !== undefined) {
      virtualPort.write(`M140 S${bed}\n`);
    }

    // Broadcast temperature update
    setTimeout(() => {
      wsManager.broadcast({
        event: 'emulator_temperature',
        data: {
          extruder: virtualPort.state.extruderTemp,
          bed: virtualPort.state.bedTemp,
          targetExtruder: virtualPort.state.targetExtruderTemp,
          targetBed: virtualPort.state.targetBedTemp
        }
      });
    }, 100);

    res.json({
      success: true,
      message: 'Temperature set successfully'
    });
  } catch (error) {
    console.error('Error setting temperature:', error);
    res.status(500).json({ error: 'Failed to set temperature', details: error.message });
  }
});

// Run emulator test
router.post('/runemulatortest', async (req, res) => {
  try {
    const { type, port } = req.body;

    // Find the emulator port
    let emulator = null;
    let emulatorPort = null;

    if (port) {
      emulator = activeEmulators.get(port);
      emulatorPort = port;
    } else {
      // Find first active emulator
      for (const [path, emu] of activeEmulators.entries()) {
        emulator = emu;
        emulatorPort = path;
        break;
      }
    }

    if (!emulator) {
      return res.status(404).json({ error: 'No active emulator found' });
    }

    const virtualPort = emulator.virtualPort;

    // Run test based on type
    if (type === 'simple_move') {
      const commands = [
        'G28',           // Home
        'G1 X50 Y50 Z10 F3000',  // Move to position
        'G1 X0 Y0 F3000',        // Return to origin
        'M114'           // Report position
      ];

      for (const cmd of commands) {
        virtualPort.write(cmd + '\n');
        await new Promise(resolve => setTimeout(resolve, 200));
      }
    }

    res.json({
      success: true,
      message: 'Test completed successfully'
    });
  } catch (error) {
    console.error('Error running test:', error);
    res.status(500).json({ error: 'Failed to run test', details: error.message });
  }
});

// Reset emulator
router.post('/resetemulator', async (req, res) => {
  try {
    const { port } = req.body;

    // Find the emulator port
    let emulator = null;

    if (port) {
      emulator = activeEmulators.get(port);
    } else {
      // Find first active emulator
      for (const [path, emu] of activeEmulators.entries()) {
        emulator = emu;
        break;
      }
    }

    if (!emulator) {
      return res.status(404).json({ error: 'No active emulator found' });
    }

    const virtualPort = emulator.virtualPort;

    // Reset state
    virtualPort.state = {
      x: 0,
      y: 0,
      z: 0,
      e: 0,
      extruderTemp: 25,
      bedTemp: 25,
      targetExtruderTemp: 0,
      targetBedTemp: 0,
      fanSpeed: 0,
      isPrinting: false,
      progress: 0
    };

    // Broadcast reset
    wsManager.broadcast({
      event: 'emulator_status',
      data: {
        status: 'Reset',
        message: 'Emulator has been reset'
      }
    });

    wsManager.broadcast({
      event: 'emulator_temperature',
      data: {
        extruder: 25,
        bed: 25,
        targetExtruder: 0,
        targetBed: 0
      }
    });

    res.json({
      success: true,
      message: 'Emulator reset successfully'
    });
  } catch (error) {
    console.error('Error resetting emulator:', error);
    res.status(500).json({ error: 'Failed to reset emulator', details: error.message });
  }
});

// Get emulator status
router.get('/emulatorstatus', async (req, res) => {
  try {
    const emulators = [];

    for (const [port, emulator] of activeEmulators.entries()) {
      const fabricator = await database.get('SELECT * FROM fabricators WHERE devicePort = ?', [port]);

      emulators.push({
        port,
        model: emulator.model,
        config: emulator.config,
        registered: !!fabricator,
        fabricator_id: fabricator?.id || null,
        state: emulator.virtualPort.state,
        started: emulator.started
      });
    }

    res.json({
      success: true,
      emulators
    });
  } catch (error) {
    console.error('Error getting emulator status:', error);
    res.status(500).json({ error: 'Failed to get emulator status', details: error.message });
  }
});

export default router;
