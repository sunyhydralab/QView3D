import express from 'express';
import { SerialPort } from '../serialport.js';
import { Printer } from '../printer.js';
import database from '../database.js';

const router = express.Router();

/**
 * POST /diagnose - Run diagnostics on printer
 * Checks connection, status, and basic commands
 *
 * Request body:
 * - device: Serial port name/path to diagnose
 *
 * Returns diagnostic results including connection status and basic command responses
 */
router.post('/diagnose', async (req, res) => {
  try {
    const { device } = req.body;

    if (!device) {
      return res.status(400).json({
        error: 'Missing required field',
        details: 'device is required'
      });
    }

    // Get fabricator by device port
    const fabricator = await database.get(
      'SELECT * FROM fabricators WHERE devicePort = ?',
      [device]
    );

    if (!fabricator) {
      return res.status(404).json({
        error: 'Device not found',
        details: `No fabricator found with device port ${device}`
      });
    }

    // Create a temporary printer instance for diagnostics
    const printer = new Printer();
    const diagnosticResults = [];

    try {
      // Check if port exists
      const ports = await SerialPort.list();
      const portExists = ports.some(p => p.path === device);

      if (!portExists) {
        diagnosticResults.push('Port not found in system');
        return res.json({
          success: false,
          message: 'Diagnosis completed with errors',
          diagnoseString: diagnosticResults.join('\n')
        });
      }

      diagnosticResults.push('Port found in system: OK');

      // Try to connect to the port
      let connectionSuccessful = false;
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          diagnosticResults.push('Connection timeout: FAILED');
          resolve();
        }, 5000);

        printer.setSerialPort(device, () => {
          clearTimeout(timeout);
          connectionSuccessful = true;
          diagnosticResults.push('Connection established: OK');
          resolve();
        }, 115200);
      });

      if (connectionSuccessful) {
        // Send basic test command (M115 - Get firmware info)
        try {
          printer._sendGcodeCommand('M115\n');
          diagnosticResults.push('Basic command test (M115): OK');
        } catch (err) {
          diagnosticResults.push('Basic command test: FAILED');
        }

        // Disconnect after test
        printer.closeSerialPort();
        diagnosticResults.push('Disconnect: OK');
      }

      return res.json({
        success: connectionSuccessful,
        message: 'Diagnosis successful',
        diagnoseString: diagnosticResults.join('\n')
      });

    } catch (error) {
      diagnosticResults.push(`Diagnostic error: ${error.message}`);
      return res.json({
        success: false,
        message: 'Diagnosis completed with errors',
        diagnoseString: diagnosticResults.join('\n')
      });
    }

  } catch (error) {
    console.error('Error during diagnosis:', error);
    res.status(500).json({
      error: 'Failed to diagnose device',
      details: error.message
    });
  }
});

/**
 * POST /repair - Attempt automatic port repair
 * Disconnects and reconnects to the printer port
 *
 * Request body:
 * - device: Serial port name/path to repair
 *
 * Returns repair status and result message
 */
router.post('/repair', async (req, res) => {
  try {
    const { device } = req.body;

    if (!device) {
      return res.status(400).json({
        error: 'Missing required field',
        details: 'device is required'
      });
    }

    // Check if port exists
    const ports = await SerialPort.list();
    const port = ports.find(p => p.path === device);

    if (!port) {
      return res.status(404).json({
        error: 'Device not found',
        details: `Port ${device} not found in system`
      });
    }

    // Get fabricator info to check model
    const fabricator = await database.get(
      'SELECT * FROM fabricators WHERE devicePort = ?',
      [device]
    );

    // Check if this is an Ender model (skip repair)
    if (fabricator && fabricator.model && fabricator.model.includes('Ender')) {
      return res.json({
        success: true,
        message: 'Repair not necessary for Ender devices.'
      });
    }

    // Create printer instance for repair
    const printer = new Printer();
    let repairSuccessful = false;

    try {
      // Close any existing connections to this port
      printer.closeSerialPort();

      // Wait a moment for port to fully close
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Attempt to reconnect
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          resolve();
        }, 5000);

        printer.setSerialPort(device, () => {
          clearTimeout(timeout);
          repairSuccessful = true;
          printer.closeSerialPort();
          resolve();
        }, 115200);
      });

      if (repairSuccessful) {
        return res.json({
          success: true,
          message: 'Repair successful.'
        });
      } else {
        return res.json({
          success: false,
          message: 'Repair failed: unable to reopen connection.'
        });
      }

    } catch (error) {
      return res.json({
        success: false,
        message: `Repair failed with error: ${error.message}`
      });
    }

  } catch (error) {
    console.error('Error during repair:', error);
    res.status(500).json({
      error: 'Failed to repair device',
      details: error.message
    });
  }
});

/**
 * POST /movehead - Manual print head control
 * Homes the printer (X/Y/Z movement to home position)
 *
 * Request body:
 * - port: Serial port name/path of the printer
 *
 * Returns success status of the homing operation
 */
router.post('/movehead', async (req, res) => {
  try {
    const { port } = req.body;

    if (!port) {
      return res.status(400).json({
        error: 'Missing required field',
        details: 'port is required'
      });
    }

    // Check if port exists
    const ports = await SerialPort.list();
    const portInfo = ports.find(p => p.path === port);

    if (!portInfo && !port.startsWith('EMU')) {
      return res.status(404).json({
        error: 'Device not found',
        details: `Port ${port} not found in system`
      });
    }

    // Create printer instance
    const printer = new Printer();
    let homeSuccessful = false;

    try {
      // Connect to printer
      await new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Connection timeout'));
        }, 5000);

        printer.setSerialPort(port, () => {
          clearTimeout(timeout);
          resolve();
        }, 115200);
      });

      // Send home command (G28)
      printer._sendGcodeCommand('G28\n');

      // Wait for homing to complete
      await new Promise(resolve => setTimeout(resolve, 2000));

      homeSuccessful = true;

      // Disconnect
      printer.closeSerialPort();

      return res.json({
        success: true,
        message: 'Head move successful'
      });

    } catch (error) {
      // Try to close port even if there was an error
      try {
        printer.closeSerialPort();
      } catch (e) {
        // Ignore close errors
      }

      return res.json({
        success: false,
        message: `Head move unsuccessful: ${error.message}`
      });
    }

  } catch (error) {
    console.error('Error moving head:', error);
    res.status(500).json({
      error: 'Failed to move head',
      details: error.message
    });
  }
});

/**
 * POST /repairports - Recovery utilities for stuck ports
 * Scans all ports and updates fabricator device paths if hardware IDs match
 * but port names have changed (common on Windows after reconnection)
 *
 * Returns list of repaired fabricators
 */
router.post('/repairports', async (req, res) => {
  try {
    // Get all available serial ports
    const ports = await SerialPort.list();

    // Get all fabricators from database
    const fabricators = await database.all('SELECT * FROM fabricators');

    const repairedFabricators = [];

    for (const port of ports) {
      // Get hardware ID without location suffix
      const hwid = port.serialNumber || '';
      const hwidWithoutLocation = hwid.split(' LOCATION=')[0];

      // Find fabricator with matching HWID
      const fabricator = fabricators.find(f => {
        const fabricatorHwid = (f.hwid || '').split(' LOCATION=')[0];
        return fabricatorHwid === hwidWithoutLocation;
      });

      if (fabricator && fabricator.devicePort !== port.path) {
        // Update the device port in database
        await database.run(
          'UPDATE fabricators SET devicePort = ? WHERE id = ?',
          [port.path, fabricator.id]
        );

        console.log(`Repaired port for fabricator ${fabricator.id}: ${fabricator.devicePort} -> ${port.path}`);

        repairedFabricators.push({
          fabricator_id: fabricator.id,
          old_port: fabricator.devicePort,
          new_port: port.path,
          Fabricator: {
            id: fabricator.id,
            name: fabricator.name,
            devicePort: port.path,
            hwid: fabricator.hwid,
            model: fabricator.model,
            status: fabricator.status
          }
        });
      }
    }

    return res.json({
      success: true,
      message: repairedFabricators.length > 0
        ? 'Printer port(s) successfully updated.'
        : 'No ports needed repair.',
      repaired: repairedFabricators
    });

  } catch (error) {
    console.error('Error repairing ports:', error);
    res.status(500).json({
      error: 'Failed to repair ports',
      details: error.message
    });
  }
});

export default router;
