/**
 * Port migration utility to handle localStorage updates
 * when default ports change between versions
 */

const STORAGE_VERSION_KEY = 'configVersion';
const BACKEND_KEY = 'activeBackend';
// Version 3.1: Restored middleware on port 8002, frontend connects through middleware
const CURRENT_VERSION = '3.1'; // Increment when breaking changes occur

export function migratePortSettings(): void {
  const storedVersion = localStorage.getItem(STORAGE_VERSION_KEY);
  const storedPort = localStorage.getItem('apiPort');
  const storedBackend = localStorage.getItem(BACKEND_KEY);

  // If no version is stored, this is either a fresh install or pre-migration data
  if (!storedVersion) {
    // Fresh install or pre-migration data - set defaults
    console.log('[Migration] Setting up v3.1 configuration (middleware-based)');
    localStorage.setItem(BACKEND_KEY, 'python'); // Default to Python backend
    localStorage.removeItem('apiPort'); // Port is now fixed at middleware (8002)
    localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
    console.log('[Migration] Migration to v3.1 completed');
  } else if (storedVersion < CURRENT_VERSION) {
    // Migrate from older versions
    console.log('[Migration] Updating to v3.1 (middleware on port 8002)');
    // Set default backend if not set
    if (!storedBackend) {
      localStorage.setItem(BACKEND_KEY, 'python');
    }
    // Remove old apiPort setting - now always uses middleware port 8002
    localStorage.removeItem('apiPort');
    localStorage.setItem(STORAGE_VERSION_KEY, CURRENT_VERSION);
    console.log('[Migration] Migration to v3.1 completed');
  }
}

/**
 * Clear all stored settings (useful for development)
 */
export function clearStoredSettings(): void {
  const debugMode = localStorage.getItem('debugMode'); // Preserve debug mode
  localStorage.removeItem('apiIPAddress');
  localStorage.removeItem('apiPort'); // Legacy, no longer used
  localStorage.removeItem(BACKEND_KEY);
  localStorage.removeItem(STORAGE_VERSION_KEY);

  // Restore debug mode if it was set
  if (debugMode) {
    localStorage.setItem('debugMode', debugMode);
  }

  // Set default backend
  localStorage.setItem(BACKEND_KEY, 'python');

  console.log('[Settings] Cleared stored API settings');
}

/**
 * Validate and fix backend settings
 */
export function validatePortSettings(): void {
  const backend = localStorage.getItem(BACKEND_KEY);
  const validBackends = ['python', 'javascript'];

  if (backend && !validBackends.includes(backend)) {
    console.warn(`[Validation] Invalid backend ${backend} detected, resetting to default`);
    localStorage.setItem(BACKEND_KEY, 'python');
  } else if (!backend) {
    // No backend set, use default
    localStorage.setItem(BACKEND_KEY, 'python');
  }

  // Clean up legacy apiPort if it exists
  localStorage.removeItem('apiPort');
}