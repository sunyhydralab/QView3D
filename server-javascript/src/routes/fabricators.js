import express from 'express';
import { SerialPort } from '../serialport.js';
import database from '../database.js';
import fabricatorManager from '../fabricatorManager.js';
import virtualSerialManager from '../virtualSerial.js';

const router = express.Router();

// Get available serial ports
router.get('/getports', async (req, res) => {
  try {
    // Get real serial ports
    const realPorts = await SerialPort.list();
    const realPortsList = realPorts.map(port => ({
      path: port.path,
      manufacturer: port.manufacturer || '',
      serialNumber: port.serialNumber || '',
      hwid: port.hwid || '',
      available: true
    }));

    // Get virtual serial ports
    const virtualPorts = virtualSerialManager.listPorts();
    const virtualPortsList = virtualPorts.map(port => ({
      path: port.path,
      manufacturer: port.manufacturer,
      serialNumber: port.serialNumber,
      hwid: `VIRTUAL-${port.path}`,
      available: true,
      isVirtual: true
    }));

    // Combine both lists
    const allPorts = [...realPortsList, ...virtualPortsList];

    res.json(allPorts);
  } catch (error) {
    console.error('Error listing ports:', error);
    res.status(500).json({ error: 'Failed to list ports', details: error.message });
  }
});

// Get all registered fabricators
router.get('/getfabricators', async (req, res) => {
  try {
    const fabricators = await database.all('SELECT * FROM fabricators ORDER BY position ASC');
    res.json(fabricators);
  } catch (error) {
    console.error('Error getting fabricators:', error);
    res.status(500).json({ error: 'Failed to get fabricators', details: error.message });
  }
});

// Register new fabricator
router.post('/register', async (req, res) => {
  try {
    const { printer } = req.body;
    const device = printer.device.serialPort;
    const name = printer.name;

    // Check if fabricator already exists
    const existing = await database.get('SELECT id FROM fabricators WHERE devicePort = ?', [device]);

    if (existing) {
      return res.status(400).json({ error: 'Fabricator already registered on this port' });
    }

    // Get max position to add new fabricator at the end
    const maxPos = await database.get('SELECT MAX(position) as max_pos FROM fabricators');
    const position = (maxPos?.max_pos || 0) + 1;

    // Insert new fabricator
    const result = await database.run(
      'INSERT INTO fabricators (name, devicePort, position, status) VALUES (?, ?, ?, ?)',
      [name, device, position, 'ready']
    );

    // Create queue for the new fabricator
    fabricatorManager.createQueue(result.id);

    res.json({
      success: true,
      message: 'Fabricator registered successfully',
      fabricator_id: result.id
    });
  } catch (error) {
    console.error('Error registering fabricator:', error);
    res.status(500).json({ error: 'Failed to register fabricator', details: error.message });
  }
});

// Delete fabricator
router.post('/deletefabricator', async (req, res) => {
  try {
    const { fabricator_id } = req.body;

    // Check if fabricator exists
    const fabricator = await database.get('SELECT id FROM fabricators WHERE id = ?', [fabricator_id]);

    if (!fabricator) {
      return res.status(404).json({ error: 'Fabricator not found' });
    }

    // Nullify fabricator_id in jobs table
    await database.run('UPDATE jobs SET fabricator_id = NULL WHERE fabricator_id = ?', [fabricator_id]);

    // Delete fabricator
    await database.run('DELETE FROM fabricators WHERE id = ?', [fabricator_id]);

    // Remove queue for the deleted fabricator
    fabricatorManager.removeQueue(fabricator_id);

    res.json({ success: true, message: 'Fabricator deleted successfully' });
  } catch (error) {
    console.error('Error deleting fabricator:', error);
    res.status(500).json({ error: 'Failed to delete fabricator', details: error.message });
  }
});

// Edit fabricator name
router.post('/editname', async (req, res) => {
  try {
    const { fabricator_id, name } = req.body;

    const fabricator = await database.get('SELECT id FROM fabricators WHERE id = ?', [fabricator_id]);

    if (!fabricator) {
      return res.status(404).json({ error: 'Fabricator not found' });
    }

    await database.run('UPDATE fabricators SET name = ? WHERE id = ?', [name, fabricator_id]);

    res.json({ success: true, message: 'Fabricator name updated successfully' });
  } catch (error) {
    console.error('Error updating fabricator name:', error);
    res.status(500).json({ error: 'Failed to update name', details: error.message });
  }
});

// Update fabricator status
router.post('/setstatus', async (req, res) => {
  try {
    const { id, status } = req.body;

    const fabricator = await database.get('SELECT id FROM fabricators WHERE id = ?', [id]);

    if (!fabricator) {
      return res.status(404).json({ error: 'Fabricator not found' });
    }

    await database.run('UPDATE fabricators SET status = ? WHERE id = ?', [status, id]);

    res.json({ success: true, message: 'Status updated successfully' });
  } catch (error) {
    console.error('Error updating status:', error);
    res.status(500).json({ error: 'Failed to update status', details: error.message });
  }
});

// Move fabricator list (reorder)
router.post('/movefabricatorlist', async (req, res) => {
  try {
    const { fabricator_ids } = req.body;

    // Update positions based on array order
    for (let i = 0; i < fabricator_ids.length; i++) {
      await database.run('UPDATE fabricators SET position = ? WHERE id = ?', [i + 1, fabricator_ids[i]]);
    }

    res.json({ success: true, message: 'Fabricator list successfully updated' });
  } catch (error) {
    console.error('Error reordering fabricators:', error);
    res.status(500).json({ error: 'Failed to reorder fabricators', details: error.message });
  }
});

// Get fabricator by ID
router.post('/getfabricatorbyid', async (req, res) => {
  try {
    const { fabricator_id } = req.body;

    const fabricator = await database.get('SELECT * FROM fabricators WHERE id = ?', [fabricator_id]);

    if (!fabricator) {
      return res.status(404).json({ error: 'Fabricator not found' });
    }

    res.json({ success: true, fabricator });
  } catch (error) {
    console.error('Error getting fabricator:', error);
    res.status(500).json({ error: 'Failed to get fabricator', details: error.message });
  }
});

// Get all unique printer models from database
router.get('/models', async (req, res) => {
  try {
    // Get unique model names from fabricators
    const models = await database.all('SELECT DISTINCT model FROM fabricators WHERE model IS NOT NULL ORDER BY model ASC');
    const modelNames = models.map(m => m.model).filter(Boolean);

    // If no models in database, return common models
    if (modelNames.length === 0) {
      return res.json(['Prusa MK3', 'Prusa MK4', 'Ender 3', 'MakerBot Replicator']);
    }

    res.json(modelNames);
  } catch (error) {
    console.error('Error getting printer models:', error);
    // Return default models on error
    res.json(['Prusa MK3', 'Prusa MK4', 'Ender 3', 'MakerBot Replicator']);
  }
});

export default router;
