/**
 * Backend Configuration
 * Defines the available backends and their connection details
 */

export default {
  backends: {
    python: {
      host: 'localhost',
      port: 8000,
      url: 'http://localhost:8000',
      ws_port: 8000,  // SocketIO runs on same port as HTTP
      emulator_port: 8004
    },
    javascript: {
      host: 'localhost',
      port: 8005,
      url: 'http://localhost:8005',
      ws_port: 8005,  // SocketIO runs on same port as HTTP
      emulator_port: 8007
    }
  },
  middleware: {
    port: 8002,
    mode: 'python'  // Default backend: 'python' or 'javascript'
  }
};
