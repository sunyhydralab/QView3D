/**
 * Emulator Routes - Simplified Mock Printer Management
 *
 * This module provides simplified mock printer functionality for frontend testing.
 * Unlike the Python backend which creates full database entries, this JavaScript
 * version keeps it simple:
 *
 * - Creates mock printers with EMU_ prefix ports (e.g., EMU_A3F7G9H2)
 * - Stores them in the database just like regular printers
 * - No complex G-code simulation or temperature tracking
 * - Just basic database entries for UI testing
 *
 * Endpoints:
 * - POST /startemulator - Create a new mock printer
 * - POST /disconnectemulator - Remove a mock printer
 * - GET /list - List all mock printers
 * - POST /updatestatus/:printerId - Update mock printer status for testing
 */
import express from 'express';
import database from '../database.js';
import virtualSerialManager from '../virtualSerial.js';
import wsManager from '../websocket.js';
import fabricatorManager from '../fabricatorManager.js';

const router = express.Router();

// Generate random string for mock serial
function generateMockSerial() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

// Start emulator - simplified to just create a mock printer in the database
router.post('/startemulator', async (req, res) => {
  try {
    const { model, config } = req.body;
    const printerName = config?.name || `Mock ${model || 'Printer'}`;

    // Generate a unique mock port with EMU_ prefix
    const mockSerial = generateMockSerial();
    const portPath = `EMU_${mockSerial}`;

    // Check if this port already exists
    const existing = await database.get('SELECT id FROM fabricators WHERE devicePort = ?', [portPath]);
    if (existing) {
      return res.status(400).json({ error: 'Mock printer with this port already exists' });
    }

    // Get max position for ordering
    const maxPos = await database.get('SELECT MAX(position) as max_pos FROM fabricators');
    const position = (maxPos?.max_pos || 0) + 1;

    // Create mock printer in database
    const result = await database.run(
      'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
      [printerName, portPath, position, 'ready']
    );

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

    console.log(`Mock printer created: ${printerName} on ${portPath}`);

    res.json({
      success: true,
      message: 'Mock printer created successfully',
      port: portPath,
      model: model || 'Mock Printer',
      printer: {
        id: result.id,
        name: printerName,
        port: portPath,
        status: 'ready'
      }
    });
  } catch (error) {
    console.error('Error creating mock printer:', error);
    res.status(500).json({ error: 'Failed to create mock printer', details: error.message });
  }
});

// Disconnect emulator - remove mock printer from database
router.post('/disconnectemulator', async (req, res) => {
  try {
    const { printerConfig, port } = req.body;
    const portPath = port || printerConfig?.port;

    if (!portPath) {
      return res.status(400).json({ error: 'No port specified' });
    }

    // Check if it's a mock printer (EMU_ prefix)
    if (!portPath.startsWith('EMU_')) {
      return res.status(400).json({ error: 'Can only disconnect mock printers' });
    }

    // Remove from database
    const fabricator = await database.get('SELECT id FROM fabricators WHERE devicePort = ?', [portPath]);
    if (fabricator) {
      await database.run('DELETE FROM fabricators WHERE id = ?', [fabricator.id]);
      fabricatorManager.removeQueue(fabricator.id);

      // Broadcast removal
      wsManager.broadcast({
        event: 'fabricator_removed',
        data: { id: fabricator.id }
      });
    }

    console.log(`Mock printer disconnected: ${portPath}`);

    res.json({
      success: true,
      message: 'Mock printer disconnected successfully'
    });
  } catch (error) {
    console.error('Error disconnecting mock printer:', error);
    res.status(500).json({ error: 'Failed to disconnect mock printer', details: error.message });
  }
});

// Register emulator - same as start emulator (for backward compatibility)
router.post('/registeremulator', async (req, res) => {
  // Just redirect to startemulator since they do the same thing now
  return router.post('/startemulator')(req, res);
});

// List all mock printers
router.get('/list', async (req, res) => {
  try {
    // Query all fabricators with EMU_ prefix
    const mockPrinters = await database.all('SELECT * FROM fabricators WHERE devicePort LIKE "EMU_%"');

    const printersList = mockPrinters.map(printer => ({
      id: printer.id,
      name: printer.name,
      model: printer.model || 'Mock Printer',
      port: printer.devicePort,
      status: printer.status
    }));

    res.json({
      success: true,
      printers: printersList
    });
  } catch (error) {
    console.error('Error listing mock printers:', error);
    res.status(500).json({ error: 'Failed to list mock printers', details: error.message });
  }
});

// Update mock printer status (for testing)
router.post('/updatestatus/:printerId', async (req, res) => {
  try {
    const { printerId } = req.params;
    const { status } = req.body;

    const validStatuses = ['ready', 'printing', 'paused', 'error', 'offline', 'maintenance'];
    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        error: `Invalid status. Must be one of: ${validStatuses.join(', ')}`
      });
    }

    // Find the fabricator
    const fabricator = await database.get('SELECT * FROM fabricators WHERE id = ?', [printerId]);

    if (!fabricator) {
      return res.status(404).json({ error: 'Printer not found' });
    }

    // Check if it's a mock printer
    if (!fabricator.devicePort.startsWith('EMU_')) {
      return res.status(400).json({ error: 'Can only update status of mock printers' });
    }

    // Update status
    await database.run('UPDATE fabricators SET status = ? WHERE id = ?', [status, printerId]);

    // Broadcast update
    wsManager.broadcast({
      event: 'fabricator_update',
      data: {
        id: printerId,
        status: status
      }
    });

    res.json({
      success: true,
      message: 'Status updated successfully',
      printer_id: printerId,
      new_status: status
    });
  } catch (error) {
    console.error('Error updating mock printer status:', error);
    res.status(500).json({ error: 'Failed to update status', details: error.message });
  }
});

// Legacy endpoints for backward compatibility (no-op responses)
router.post('/setemulatortemperature', async (req, res) => {
  res.json({ success: true, message: 'Temperature setting not needed for mock printers' });
});

router.post('/runemulatortest', async (req, res) => {
  res.json({ success: true, message: 'Test completed (mock - no actual test run)' });
});

router.post('/resetemulator', async (req, res) => {
  res.json({ success: true, message: 'Reset completed (mock - no state to reset)' });
});

router.get('/emulatorstatus', async (req, res) => {
  // Redirect to list endpoint
  return router.get('/list')(req, res);
});

export default router;
