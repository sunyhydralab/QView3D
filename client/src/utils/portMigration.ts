/**
 * Port migration utility to handle localStorage updates
 * when default ports change between versions
 */

const STORAGE_VERSION_KEY = 'configVersion';
// Bump version to force migration of API port to middleware 8002
const CURRENT_VERSION = '2.1'; // Increment when breaking changes occur

export function migratePortSettings(): void {
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  const storedPort = localStorage.getItem('apiPort');

  // If no version is stored, this is either a fresh install or pre-migration data
  if (!storedVersion) {
    // Check if we have old port 8000 or 3500 stored
    if (storedPort === '8000' || storedPort === '3500') {
      console.log('[Migration] Updating port to 8002 (middleware)');
      localStorage.setItem('apiPort', '8002');
      localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
      console.log('[Migration] Port migration completed');
    } else if (!storedPort) {
      // Fresh install, just set the version
      localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
    }
  } else if (storedVersion < CURRENT_VERSION) {
    // Migrate old ports (3500 or 8000) to new middleware port 8002
    if (storedPort === '3500' || storedPort === '8000') {
      console.log('[Migration] Updating legacy port to 8002 (middleware)');
      localStorage.setItem('apiPort', '8002');
    }
    localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
  }
}

/**
 * Clear all stored settings (useful for development)
 */
export function clearStoredSettings(): void {
  const debugMode = localStorage.getItem('debugMode'); // Preserve debug mode
  localStorage.removeItem('apiIPAddress');
  localStorage.removeItem('apiPort');
  localStorage.removeItem(STORAGE_VERSION_KEY);

  // Restore debug mode if it was set
  if (debugMode) {
    localStorage.setItem('debugMode', debugMode);
  }

  console.log('[Settings] Cleared stored API settings');
}

/**
 * Validate and fix port settings
 */
export function validatePortSettings(): void {
  const port = localStorage.getItem('apiPort');
  const validPorts = ['8002', '8000', '8005']; // Valid port options (middleware, python, js)

  if (port && !validPorts.includes(port)) {
    console.warn(`[Validation] Invalid port ${port} detected, resetting to default`);
    localStorage.removeItem('apiPort');
  }
}