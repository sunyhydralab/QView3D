/**
 * Port migration utility to handle localStorage updates
 * when default ports change between versions
 */

const STORAGE_VERSION_KEY = 'configVersion';
const CURRENT_VERSION = '2.0'; // Increment when breaking changes occur

export function migratePortSettings(): void {
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  const storedPort = localStorage.getItem('apiPort');

  // If no version is stored, this is either a fresh install or pre-migration data
  if (!storedVersion) {
    // Check if we have old port 8000 stored
    if (storedPort === '8000') {
      console.log('[Migration] Updating port from 8000 to 3500 (middleware)');
      localStorage.setItem('apiPort', '3500');
      localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
      console.log('[Migration] Port migration completed');
    } else if (!storedPort) {
      // Fresh install, just set the version
      localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
    }
  } else if (storedVersion < CURRENT_VERSION) {
    // Handle future migrations here
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
  const validPorts = ['3500', '8000', '3001']; // Valid port options

  if (port && !validPorts.includes(port)) {
    console.warn(`[Validation] Invalid port ${port} detected, resetting to default`);
    localStorage.removeItem('apiPort');
  }
}