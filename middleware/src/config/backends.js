import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load config from server/config/config.json
const configPath = path.join(__dirname, '../../..', 'server', 'config', 'config.json');

let config = {};

try {
  const configData = fs.readFileSync(configPath, 'utf8');
  config = JSON.parse(configData);
} catch (error) {
  console.error('Failed to load config.json:', error.message);
  process.exit(1);
}

// Default values if not in config
const defaultBackends = {
  python: {
    name: 'Python',
    url: 'http://localhost:8000',
    ws_port: 8001,
    emulator_port: 8004,
    healthEndpoint: '/health',
    capabilities: ['database', 'job_management', 'full_api']
  },
  javascript: {
    name: 'JavaScript',
    url: 'http://localhost:8005',
    ws_port: 8006,
    emulator_port: 8007,
    healthEndpoint: '/health',
    capabilities: ['serial_communication', 'printer_control', 'gcode_processing']
  }
};

const defaultMiddleware = {
  mode: 'python',
  port: 8002,
  ws_port: 8003
};

// Merge config with defaults
export const backends = {
  python: {
    ...defaultBackends.python,
    ...(config.backends?.python || {})
  },
  javascript: {
    ...defaultBackends.javascript,
    ...(config.backends?.javascript || {})
  }
};

export const middleware = {
  ...defaultMiddleware,
  ...(config.middleware || {})
};

export const routingMode = middleware.mode;

// CORS configuration
export const corsOptions = {
  origin: '*',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

export default {
  backends,
  middleware,
  routingMode,
  corsOptions
};
