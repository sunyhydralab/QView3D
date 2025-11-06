/**
 * Virtual Serial Port for Emulator
 * Simplified mock serial port for basic testing without complex simulation
 */
import { EventEmitter } from 'events';

export class VirtualSerialPort extends EventEmitter {
  constructor(path, options = {}) {
    super();
    this.path = path;
    this.baudRate = options.baudRate || 115200;
    this.isOpen = false;
  }

  /**
   * Open the virtual serial port
   */
  open(callback) {
    setTimeout(() => {
      this.isOpen = true;
      this.emit('open');

      // Send basic ready message
      setTimeout(() => {
        this.emit('data', Buffer.from('start\n'));
        this.emit('data', Buffer.from('echo:Mock Printer Ready\n'));
      }, 50);

      if (callback) callback(null);
    }, 10);
  }

  /**
   * Close the virtual serial port
   */
  close(callback) {
    this.isOpen = false;
    this.emit('close');
    if (callback) callback(null);
  }

  /**
   * Write data to the virtual serial port
   * Just returns 'ok' for all commands - no actual processing
   */
  write(data, callback) {
    if (!this.isOpen) {
      const error = new Error('Port is not open');
      if (callback) callback(error);
      return;
    }

    const command = data.toString().trim();
    console.log(`[MockSerial ${this.path}] Received: ${command}`);

    // Just send 'ok' response for any command
    setTimeout(() => {
      this.emit('data', Buffer.from('ok\n'));
      if (callback) callback(null);
    }, 10);
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
 * Manages mock serial ports for basic testing
 */
export class VirtualSerialPortManager {
  constructor() {
    this.ports = new Map();
    this.nextPortNumber = 1;
  }

  /**
   * Create a new virtual serial port with EMU_ prefix
   */
  createPort(name = null) {
    const portPath = name || `EMU_${String(this.nextPortNumber++).padStart(3, '0')}`;
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
      manufacturer: 'QView3D_Mock',
      serialNumber: path,
      vendorId: '0x0000',
      productId: '0x0000'
    }));
  }

  /**
   * Check if a port is virtual/mock
   */
  isVirtualPort(path) {
    return this.ports.has(path) || (path && path.startsWith('EMU_'));
  }
}

// Export singleton instance
const virtualSerialManager = new VirtualSerialPortManager();
export default virtualSerialManager;
