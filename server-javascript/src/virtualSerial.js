/**
 * Virtual Serial Port for Emulator
 * Simulates a real serial port connection for testing without physical hardware
 */
import { EventEmitter } from 'events';

export class VirtualSerialPort extends EventEmitter {
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.baudRate = options.baudRate || 115200;
    this.isOpen = false;
    this.buffer = '';

    // Simulated printer state
    this.state = {
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

    // Temperature simulation interval
    this.tempInterval = null;
  }

  /**
   * Open the virtual serial port
   */
  open(callback) {
    setTimeout(() => {
      this.isOpen = true;
      this.emit('open');

      // Start temperature simulation
      this.startTemperatureSimulation();

      // Send ready message
      setTimeout(() => {
        this.emit('data', Buffer.from('start\n'));
        this.emit('data', Buffer.from('echo:Marlin ready\n'));
      }, 100);

      if (callback) callback(null);
    }, 10);
  }

  /**
   * Close the virtual serial port
   */
  close(callback) {
    this.isOpen = false;
    this.stopTemperatureSimulation();
    this.emit('close');
    if (callback) callback(null);
  }

  /**
   * Write data to the virtual serial port
   */
  write(data, callback) {
    if (!this.isOpen) {
      const error = new Error('Port is not open');
      if (callback) callback(error);
      return;
    }

    const command = data.toString().trim();
    console.log(`[VirtualSerial] Received: ${command}`);

    // Process the G-code command
    setTimeout(() => {
      this.processGCode(command);
      if (callback) callback(null);
    }, 10);
  }

  /**
   * Process G-code commands
   */
  processGCode(command) {
    const cmd = command.toUpperCase().trim();

    // G28 - Home all axes
    if (cmd.startsWith('G28')) {
      this.state.x = 0;
      this.state.y = 0;
      this.state.z = 0;
      this.emit('data', Buffer.from('X:0.00 Y:0.00 Z:0.00 E:0.00 Count X:0 Y:0 Z:0\n'));
      this.emit('data', Buffer.from('ok\n'));
    }

    // G1 - Linear move
    else if (cmd.startsWith('G1')) {
      const xMatch = cmd.match(/X([-\d.]+)/);
      const yMatch = cmd.match(/Y([-\d.]+)/);
      const zMatch = cmd.match(/Z([-\d.]+)/);
      const eMatch = cmd.match(/E([-\d.]+)/);

      if (xMatch) this.state.x = parseFloat(xMatch[1]);
      if (yMatch) this.state.y = parseFloat(yMatch[1]);
      if (zMatch) this.state.z = parseFloat(zMatch[1]);
      if (eMatch) this.state.e = parseFloat(eMatch[1]);

      this.emit('data', Buffer.from('ok\n'));
    }

    // M104 - Set extruder temperature
    else if (cmd.startsWith('M104')) {
      const sMatch = cmd.match(/S([-\d.]+)/);
      if (sMatch) {
        this.state.targetExtruderTemp = parseFloat(sMatch[1]);
      }
      this.emit('data', Buffer.from('ok\n'));
    }

    // M109 - Set extruder temperature and wait
    else if (cmd.startsWith('M109')) {
      const sMatch = cmd.match(/S([-\d.]+)/);
      if (sMatch) {
        this.state.targetExtruderTemp = parseFloat(sMatch[1]);
      }
      this.emit('data', Buffer.from('ok\n'));
    }

    // M140 - Set bed temperature
    else if (cmd.startsWith('M140')) {
      const sMatch = cmd.match(/S([-\d.]+)/);
      if (sMatch) {
        this.state.targetBedTemp = parseFloat(sMatch[1]);
      }
      this.emit('data', Buffer.from('ok\n'));
    }

    // M190 - Set bed temperature and wait
    else if (cmd.startsWith('M190')) {
      const sMatch = cmd.match(/S([-\d.]+)/);
      if (sMatch) {
        this.state.targetBedTemp = parseFloat(sMatch[1]);
      }
      this.emit('data', Buffer.from('ok\n'));
    }

    // M105 - Get temperatures
    else if (cmd.startsWith('M105')) {
      const tempReport = `ok T:${this.state.extruderTemp.toFixed(1)} /${this.state.targetExtruderTemp.toFixed(1)} B:${this.state.bedTemp.toFixed(1)} /${this.state.targetBedTemp.toFixed(1)}\n`;
      this.emit('data', Buffer.from(tempReport));
    }

    // M106 - Set fan speed
    else if (cmd.startsWith('M106')) {
      const sMatch = cmd.match(/S([-\d.]+)/);
      if (sMatch) {
        this.state.fanSpeed = parseFloat(sMatch[1]);
      }
      this.emit('data', Buffer.from('ok\n'));
    }

    // M107 - Turn off fan
    else if (cmd.startsWith('M107')) {
      this.state.fanSpeed = 0;
      this.emit('data', Buffer.from('ok\n'));
    }

    // M114 - Get current position
    else if (cmd.startsWith('M114')) {
      const posReport = `X:${this.state.x.toFixed(2)} Y:${this.state.y.toFixed(2)} Z:${this.state.z.toFixed(2)} E:${this.state.e.toFixed(2)} Count X:0 Y:0 Z:0\n`;
      this.emit('data', Buffer.from(posReport));
      this.emit('data', Buffer.from('ok\n'));
    }

    // M115 - Get firmware info
    else if (cmd.startsWith('M115')) {
      this.emit('data', Buffer.from('FIRMWARE_NAME:QView3D_Emulator FIRMWARE_VERSION:1.0.0 MACHINE_TYPE:Virtual_Printer\n'));
      this.emit('data', Buffer.from('ok\n'));
    }

    // Default response for unrecognized commands
    else {
      this.emit('data', Buffer.from('ok\n'));
    }
  }

  /**
   * Start simulating temperature changes
   */
  startTemperatureSimulation() {
    if (this.tempInterval) return;

    this.tempInterval = setInterval(() => {
      // Simulate extruder heating/cooling
      if (this.state.extruderTemp < this.state.targetExtruderTemp) {
        this.state.extruderTemp = Math.min(
          this.state.extruderTemp + 2,
          this.state.targetExtruderTemp
        );
      } else if (this.state.extruderTemp > this.state.targetExtruderTemp) {
        this.state.extruderTemp = Math.max(
          this.state.extruderTemp - 1,
          this.state.targetExtruderTemp
        );
      }

      // Simulate bed heating/cooling
      if (this.state.bedTemp < this.state.targetBedTemp) {
        this.state.bedTemp = Math.min(
          this.state.bedTemp + 1,
          this.state.targetBedTemp
        );
      } else if (this.state.bedTemp > this.state.targetBedTemp) {
        this.state.bedTemp = Math.max(
          this.state.bedTemp - 0.5,
          this.state.targetBedTemp
        );
      }
    }, 1000);
  }

  /**
   * Stop temperature simulation
   */
  stopTemperatureSimulation() {
    if (this.tempInterval) {
      clearInterval(this.tempInterval);
      this.tempInterval = null;
    }
  }

  /**
   * Drain the port (no-op for virtual port)
   */
  drain(callback) {
    if (callback) callback(null);
  }

  /**
   * Flush the port (no-op for virtual port)
   */
  flush(callback) {
    if (callback) callback(null);
  }
}

/**
 * Virtual Serial Port Manager
 * Manages virtual serial ports for emulators
 */
export class VirtualSerialPortManager {
  constructor() {
    this.ports = new Map();
    this.nextPortNumber = 1;
  }

  /**
   * Create a new virtual serial port
   */
  createPort(name = null) {
    const portPath = name || `EMU-${String(this.nextPortNumber++).padStart(3, '0')}`;
    const port = new VirtualSerialPort(portPath);
    this.ports.set(portPath, port);
    return portPath;
  }

  /**
   * Get a virtual serial port
   */
  getPort(path) {
    return this.ports.get(path);
  }

  /**
   * Delete a virtual serial port
   */
  deletePort(path) {
    const port = this.ports.get(path);
    if (port && port.isOpen) {
      port.close();
    }
    return this.ports.delete(path);
  }

  /**
   * List all virtual serial ports
   */
  listPorts() {
    return Array.from(this.ports.keys()).map(path => ({
      path,
      manufacturer: 'QView3D',
      serialNumber: path,
      vendorId: '0x0000',
      productId: '0x0000'
    }));
  }

  /**
   * Check if a port is virtual
   */
  isVirtualPort(path) {
    return this.ports.has(path);
  }
}

// Export singleton instance
const virtualSerialManager = new VirtualSerialPortManager();
export default virtualSerialManager;
