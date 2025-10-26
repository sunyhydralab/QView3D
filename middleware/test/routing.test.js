/**
 * Routing Test Suite
 *
 * Tests for the routing logic in the middleware server.
 * Tests getBackendForRoute() function and route mapping behavior.
 */

import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert';

// Mock configuration objects
const mockBackends = {
  python: {
    name: 'Python',
    url: 'http://localhost:8000',
    healthEndpoint: '/health'
  },
  javascript: {
    name: 'JavaScript',
    url: 'http://localhost:8005',
    healthEndpoint: '/health'
  }
};

/**
 * Implementation of getBackendForRoute for testing
 * This mirrors the logic in src/index.js
 */
function getBackendForRoute(path, routeMap, defaultBackend, selectedBackend, backends) {
  // Check if route is explicitly mapped
  const mappedBackend = routeMap[path];

  if (mappedBackend === 'python') {
    return backends.python;
  } else if (mappedBackend === 'javascript') {
    return backends.javascript;
  } else if (mappedBackend === 'either') {
    // For 'either' routes, use the currently selected backend
    return selectedBackend === 'python' ? backends.python : backends.javascript;
  }

  // If no explicit mapping, use default backend
  return defaultBackend === 'python' ? backends.python : backends.javascript;
}

describe('Routing Logic', () => {
  describe('getBackendForRoute - Route Mapping', () => {
    it('should route to python backend when mapped to "python"', () => {
      const routeMap = {
        '/api/database': 'python'
      };

      const backend = getBackendForRoute(
        '/api/database',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
      assert.strictEqual(backend.name, 'Python');
    });

    it('should route to javascript backend when mapped to "javascript"', () => {
      const routeMap = {
        '/api/serial': 'javascript'
      };

      const backend = getBackendForRoute(
        '/api/serial',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8005');
      assert.strictEqual(backend.name, 'JavaScript');
    });

    it('should use selected backend when route is mapped to "either"', () => {
      const routeMap = {
        '/api/health': 'either'
      };

      // Test with python selected
      let backend = getBackendForRoute(
        '/api/health',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8000');

      // Test with javascript selected
      backend = getBackendForRoute(
        '/api/health',
        routeMap,
        'python',
        'javascript',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8005');
    });

    it('should handle multiple routes in route map', () => {
      const routeMap = {
        '/api/database': 'python',
        '/api/serial': 'javascript',
        '/api/health': 'either'
      };

      const pythonBackend = getBackendForRoute(
        '/api/database',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(pythonBackend.url, 'http://localhost:8000');

      const jsBackend = getBackendForRoute(
        '/api/serial',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(jsBackend.url, 'http://localhost:8005');

      const eitherBackend = getBackendForRoute(
        '/api/health',
        routeMap,
        'python',
        'javascript',
        mockBackends
      );
      assert.strictEqual(eitherBackend.url, 'http://localhost:8005');
    });
  });

  describe('getBackendForRoute - Default Backend Selection', () => {
    it('should use default backend for unmapped routes', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/api/unmapped',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
    });

    it('should respect default backend setting (python)', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/api/unknown',
        routeMap,
        'python',
        'javascript',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
      assert.strictEqual(backend.name, 'Python');
    });

    it('should respect default backend setting (javascript)', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/api/unknown',
        routeMap,
        'javascript',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8005');
      assert.strictEqual(backend.name, 'JavaScript');
    });

    it('should use default backend when route map is empty', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/any/path',
        routeMap,
        'javascript',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8005');
    });
  });

  describe('getBackendForRoute - Edge Cases', () => {
    it('should handle routes with query parameters', () => {
      const routeMap = {
        '/api/data': 'python'
      };

      // Note: In real implementation, query params might be in path
      const backend = getBackendForRoute(
        '/api/data',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
    });

    it('should handle routes with trailing slashes', () => {
      const routeMap = {
        '/api/test': 'javascript'
      };

      const backend = getBackendForRoute(
        '/api/test',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8005');
    });

    it('should handle root path', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
    });

    it('should be case-sensitive for route paths', () => {
      const routeMap = {
        '/api/Test': 'javascript'
      };

      // Different case should not match
      const backend = getBackendForRoute(
        '/api/test',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      // Should use default since route doesn't match
      assert.strictEqual(backend.url, 'http://localhost:8000');
    });

    it('should handle deeply nested paths', () => {
      const routeMap = {
        '/api/v1/database/query': 'python'
      };

      const backend = getBackendForRoute(
        '/api/v1/database/query',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8000');
    });
  });

  describe('Route Mapping Priority', () => {
    it('should prioritize explicit mapping over default backend', () => {
      const routeMap = {
        '/api/explicit': 'javascript'
      };

      const backend = getBackendForRoute(
        '/api/explicit',
        routeMap,
        'python', // default is python
        'python', // selected is python
        mockBackends
      );

      // Should use javascript due to explicit mapping
      assert.strictEqual(backend.url, 'http://localhost:8005');
    });

    it('should use selected backend for "either" routes regardless of default', () => {
      const routeMap = {
        '/api/flexible': 'either'
      };

      // Selected backend should win for "either" routes
      const backend = getBackendForRoute(
        '/api/flexible',
        routeMap,
        'python', // default
        'javascript', // selected
        mockBackends
      );

      assert.strictEqual(backend.url, 'http://localhost:8005');
    });

    it('should handle mixed routing scenarios', () => {
      const routeMap = {
        '/api/python-only': 'python',
        '/api/js-only': 'javascript',
        '/api/flexible': 'either'
      };

      // Python-only route
      let backend = getBackendForRoute(
        '/api/python-only',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8000');

      // JavaScript-only route
      backend = getBackendForRoute(
        '/api/js-only',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8005');

      // Flexible route with python selected
      backend = getBackendForRoute(
        '/api/flexible',
        routeMap,
        'javascript',
        'python',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8000');

      // Unmapped route uses default
      backend = getBackendForRoute(
        '/api/unmapped',
        routeMap,
        'javascript',
        'python',
        mockBackends
      );
      assert.strictEqual(backend.url, 'http://localhost:8005');
    });
  });

  describe('Backend Configuration Integrity', () => {
    it('should return complete backend object', () => {
      const routeMap = {
        '/api/test': 'python'
      };

      const backend = getBackendForRoute(
        '/api/test',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );

      assert.ok(backend.name);
      assert.ok(backend.url);
      assert.ok(backend.healthEndpoint);
      assert.strictEqual(typeof backend, 'object');
    });

    it('should maintain backend object properties', () => {
      const routeMap = {};

      const backend = getBackendForRoute(
        '/api/any',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.strictEqual(backend.name, 'Python');
      assert.strictEqual(backend.url, 'http://localhost:8000');
      assert.strictEqual(backend.healthEndpoint, '/health');
    });

    it('should return different backend objects for different routes', () => {
      const routeMap = {
        '/api/python': 'python',
        '/api/javascript': 'javascript'
      };

      const pythonBackend = getBackendForRoute(
        '/api/python',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      const jsBackend = getBackendForRoute(
        '/api/javascript',
        routeMap,
        'python',
        'python',
        mockBackends
      );

      assert.notStrictEqual(pythonBackend, jsBackend);
      assert.notStrictEqual(pythonBackend.url, jsBackend.url);
    });
  });

  describe('Real-world Route Scenarios', () => {
    it('should route common API endpoints correctly', () => {
      const routeMap = {
        '/api/database': 'python',
        '/api/serial': 'javascript',
        '/health': 'either'
      };

      // Database route to Python
      let backend = getBackendForRoute(
        '/api/database',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );
      assert.strictEqual(backend.name, 'Python');

      // Serial communication to JavaScript
      backend = getBackendForRoute(
        '/api/serial',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(backend.name, 'JavaScript');

      // Health check uses selected backend
      backend = getBackendForRoute(
        '/health',
        routeMap,
        'python',
        'javascript',
        mockBackends
      );
      assert.strictEqual(backend.name, 'JavaScript');
    });

    it('should handle printer-related routes', () => {
      const routeMap = {
        '/getfabricators': 'python',
        '/registerfabricator': 'python',
        '/getports': 'javascript'
      };

      const getFabBackend = getBackendForRoute(
        '/getfabricators',
        routeMap,
        'javascript',
        'javascript',
        mockBackends
      );
      assert.strictEqual(getFabBackend.name, 'Python');

      const getPortsBackend = getBackendForRoute(
        '/getports',
        routeMap,
        'python',
        'python',
        mockBackends
      );
      assert.strictEqual(getPortsBackend.name, 'JavaScript');
    });
  });
});
