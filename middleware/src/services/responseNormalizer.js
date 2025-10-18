// Map JavaScript PrinterState to Python status strings
const PRINTER_STATE_MAP = {
  0: 'offline',    // NOT_CONNECTED
  1: 'ready',      // READY
  2: 'printing',   // PRINTING
  3: 'connecting', // CONNECTING
  4: 'paused',     // PAUSED
  5: 'error'       // ERROR
};

export class ResponseNormalizer {
  constructor() {
    this.normalizers = {
      '/getprinterinfo': this.normalizePrinterInfo.bind(this),
      '/api/serial/ports': this.normalizePortList.bind(this),
      '/getjobs': this.normalizeJobList.bind(this)
    };
  }

  // Main normalize method
  normalize(data, sourceBackend, path) {
    // If Python backend or no normalizer needed, return as-is
    if (sourceBackend === 'python' || !this.normalizers[path]) {
      return data;
    }

    // Apply specific normalizer
    return this.normalizers[path](data, sourceBackend);
  }

  normalizePrinterInfo(data, sourceBackend) {
    if (!Array.isArray(data)) {
      return data;
    }

    return data.map(printer => ({
      id: printer.id,
      name: printer.name || printer.model,
      description: printer.description || printer.modelName || '',
      hwid: printer.hwid || printer.serialNumber || '',
      device: printer.device || {
        serialPort: printer.port || '',
        baudRate: printer.baudRate || 115200
      },
      status: this.mapPrinterState(printer.state || printer.status),
      queue: printer.jobs || printer.queue || []
    }));
  }

  normalizePortList(data, sourceBackend) {
    // Normalize serial port list format
    if (!Array.isArray(data)) {
      return data;
    }

    return data.map(port => ({
      port: port.path || port.port,
      manufacturer: port.manufacturer || '',
      serialNumber: port.serialNumber || '',
      available: port.available !== false
    }));
  }

  normalizeJobList(data, sourceBackend) {
    if (!Array.isArray(data)) {
      return data;
    }

    return data.map(job => ({
      id: job.id,
      name: job.scriptName || job.name,
      file: job.file,
      file_name_original: job.fileName || job.file_name_original,
      status: job.state || job.status,
      progress: job.progress || 0,
      printerid: job.printerId || job.printerid,
      td_id: job.ticketId || job.td_id || 0
    }));
  }

  mapPrinterState(state) {
    // Handle numeric state
    if (typeof state === 'number') {
      return PRINTER_STATE_MAP[state] || 'unknown';
    }
    // Already a string
    return state;
  }
}
