import { routeMap, defaultBackend } from '../config/routes.js';
import logger from '../utils/logger.js';

export class BackendSelector {
  constructor(backends, routingMode, healthMonitor) {
    this.backends = backends;
    this.mode = routingMode;
    this.healthMonitor = healthMonitor;
    this.routeMap = routeMap;
  }

  // Match route against patterns
  matchRoute(path, pattern) {
    if (pattern.includes('*')) {
      const regex = new RegExp('^' + pattern.replace('*', '.*') + '$');
      return regex.test(path);
    }
    return path === pattern;
  }

  // Select backend based on route and mode
  selectBackend(req) {
    // Force mode selection
    if (this.mode === 'python') {
      return this.backends.python;
    }

    if (this.mode === 'javascript') {
      return this.backends.javascript;
    }

    // Hybrid mode - intelligent routing
    const path = req.path;

    // Check route map for specific routes
    for (const [pattern, backendName] of Object.entries(this.routeMap)) {
      if (this.matchRoute(path, pattern)) {
        // Handle 'either' - load balance between backends
        if (backendName === 'either') {
          return this.selectHealthyBackend();
        }

        const backend = this.backends[backendName];

        // If preferred backend is healthy, use it
        if (this.healthMonitor.isBackendHealthy(backendName)) {
          logger.debug(`Routing ${path} to ${backendName} backend`);
          return backend;
        }

        // Try alternate backend if primary is down
        const alternate = this.getAlternateBackend(backendName);
        if (alternate && this.healthMonitor.isBackendHealthy(alternate.name)) {
          logger.warn(`Primary backend ${backendName} unhealthy, using ${alternate.name}`);
          return alternate.backend;
        }

        // Return original even if unhealthy (will fail with proper error)
        return backend;
      }
    }

    // Default to Python backend
    logger.debug(`No route match for ${path}, using default backend`);
    return this.backends[defaultBackend];
  }

  // Select a healthy backend for load balancing
  selectHealthyBackend() {
    const pythonHealthy = this.healthMonitor.isBackendHealthy('python');
    const javascriptHealthy = this.healthMonitor.isBackendHealthy('javascript');

    // Both healthy - alternate based on a simple round-robin
    if (pythonHealthy && javascriptHealthy) {
      this.roundRobinCounter = (this.roundRobinCounter || 0) + 1;
      return this.roundRobinCounter % 2 === 0
        ? this.backends.python
        : this.backends.javascript;
    }

    // Only one healthy - use the healthy one
    if (pythonHealthy) return this.backends.python;
    if (javascriptHealthy) return this.backends.javascript;

    // None healthy - default to python
    return this.backends.python;
  }

  getAlternateBackend(currentBackendName) {
    // Simple alternation between python and javascript
    if (currentBackendName === 'python') {
      return { name: 'javascript', backend: this.backends.javascript };
    }
    return { name: 'python', backend: this.backends.python };
  }

  getBackendUrl(req) {
    const backend = this.selectBackend(req);
    return backend.url;
  }
}
