/**
 * Health Check Test Suite
 *
 * Tests for the HealthChecker class that monitors backend service health.
 */

import { describe, it, beforeEach, afterEach, mock } from 'node:test';
import assert from 'node:assert';
import { HealthChecker } from '../src/healthCheck.js';

// Mock backends configuration
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

describe('HealthChecker', () => {
  let healthChecker;
  let originalFetch;

  beforeEach(() => {
    // Save original fetch
    originalFetch = global.fetch;
  });

  afterEach(() => {
    // Restore original fetch
    global.fetch = originalFetch;

    // Stop health checker if running
    if (healthChecker) {
      healthChecker.stop();
    }
  });

  describe('Constructor and Initialization', () => {
    it('should initialize with provided backends and interval', () => {
      healthChecker = new HealthChecker(mockBackends, 5000);

      assert.strictEqual(healthChecker.interval, 5000);
      assert.strictEqual(healthChecker.timeout, 5000);
      assert.deepStrictEqual(Object.keys(healthChecker.backends), ['python', 'javascript']);
    });

    it('should initialize status for all backends', () => {
      healthChecker = new HealthChecker(mockBackends);

      const status = healthChecker.getAllStatus();
      assert.ok(status.python);
      assert.ok(status.javascript);

      assert.strictEqual(status.python.status, 'healthy');
      assert.strictEqual(status.python.consecutiveFailures, 0);
      assert.strictEqual(status.javascript.status, 'healthy');
      assert.strictEqual(status.javascript.consecutiveFailures, 0);
    });

    it('should use default interval if not provided', () => {
      healthChecker = new HealthChecker(mockBackends);
      assert.strictEqual(healthChecker.interval, 10000);
    });
  });

  describe('Backend Status Tracking', () => {
    beforeEach(() => {
      healthChecker = new HealthChecker(mockBackends, 1000);
    });

    it('should get status for a specific backend', () => {
      const status = healthChecker.getStatus('python');
      assert.ok(status);
      assert.strictEqual(status.status, 'healthy');
    });

    it('should return null for unknown backend', () => {
      const status = healthChecker.getStatus('unknown');
      assert.strictEqual(status, null);
    });

    it('should get all backend statuses', () => {
      const allStatus = healthChecker.getAllStatus();
      assert.ok(allStatus.python);
      assert.ok(allStatus.javascript);
    });

    it('should check if backend is healthy', () => {
      assert.strictEqual(healthChecker.isHealthy('python'), true);
      assert.strictEqual(healthChecker.isHealthy('javascript'), true);
    });

    it('should check if backend is down', () => {
      assert.strictEqual(healthChecker.isDown('python'), false);
      assert.strictEqual(healthChecker.isDown('javascript'), false);
    });
  });

  describe('Health Check Functionality', () => {
    beforeEach(() => {
      healthChecker = new HealthChecker(mockBackends, 1000);
    });

    it('should mark backend as healthy on successful check', async () => {
      // Mock successful response
      global.fetch = mock.fn(async () => ({
        ok: true,
        status: 200
      }));

      await healthChecker.checkBackend('python');

      const status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'healthy');
      assert.strictEqual(status.consecutiveFailures, 0);
      assert.ok(status.responseTime !== null);
      assert.ok(status.lastCheck !== null);
      assert.strictEqual(status.lastError, null);
    });

    it('should mark backend as unhealthy on first failure', async () => {
      // Mock failed response
      global.fetch = mock.fn(async () => ({
        ok: false,
        status: 500
      }));

      await healthChecker.checkBackend('python');

      const status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'unhealthy');
      assert.strictEqual(status.consecutiveFailures, 1);
      assert.ok(status.lastError);
    });

    it('should mark backend as down after 3 consecutive failures', async () => {
      // Mock failed response
      global.fetch = mock.fn(async () => ({
        ok: false,
        status: 500
      }));

      // First failure - should be unhealthy
      await healthChecker.checkBackend('python');
      let status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'unhealthy');
      assert.strictEqual(status.consecutiveFailures, 1);

      // Second failure - should still be unhealthy
      await healthChecker.checkBackend('python');
      status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'unhealthy');
      assert.strictEqual(status.consecutiveFailures, 2);

      // Third failure - should be down
      await healthChecker.checkBackend('python');
      status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'down');
      assert.strictEqual(status.consecutiveFailures, 3);
    });

    it('should handle network errors', async () => {
      // Mock network error
      global.fetch = mock.fn(async () => {
        throw new Error('Network error');
      });

      await healthChecker.checkBackend('python');

      const status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'unhealthy');
      assert.strictEqual(status.lastError, 'Network error');
      assert.strictEqual(status.responseTime, null);
    });

    it('should handle timeout errors', async () => {
      // Mock timeout - create a promise that never resolves until aborted
      global.fetch = mock.fn(async (url, options) => {
        return new Promise((resolve, reject) => {
          options.signal.addEventListener('abort', () => {
            const error = new Error('The operation was aborted');
            error.name = 'AbortError';
            reject(error);
          });
        });
      });

      await healthChecker.checkBackend('python');

      const status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'unhealthy');
      assert.strictEqual(status.lastError, 'Request timeout');
    });

    it('should check all backends', async () => {
      // Mock successful response for all
      global.fetch = mock.fn(async () => ({
        ok: true,
        status: 200
      }));

      await healthChecker.checkAll();

      const pythonStatus = healthChecker.getStatus('python');
      const jsStatus = healthChecker.getStatus('javascript');

      assert.strictEqual(pythonStatus.status, 'healthy');
      assert.strictEqual(jsStatus.status, 'healthy');
    });

    it('should reset consecutive failures on recovery', async () => {
      // First, simulate failure
      global.fetch = mock.fn(async () => ({
        ok: false,
        status: 500
      }));

      await healthChecker.checkBackend('python');
      let status = healthChecker.getStatus('python');
      assert.strictEqual(status.consecutiveFailures, 1);

      // Now simulate recovery
      global.fetch = mock.fn(async () => ({
        ok: true,
        status: 200
      }));

      await healthChecker.checkBackend('python');
      status = healthChecker.getStatus('python');
      assert.strictEqual(status.status, 'healthy');
      assert.strictEqual(status.consecutiveFailures, 0);
      assert.strictEqual(status.lastError, null);
    });
  });

  describe('Monitoring Start and Stop', () => {
    beforeEach(() => {
      healthChecker = new HealthChecker(mockBackends, 100);
    });

    it('should start monitoring and set interval', async () => {
      // Mock successful response
      global.fetch = mock.fn(async () => ({
        ok: true,
        status: 200
      }));

      healthChecker.start();

      assert.ok(healthChecker.intervalId !== null);

      // Wait a bit to ensure initial check runs
      await new Promise(resolve => setTimeout(resolve, 50));

      // Verify that checkAll was called
      const status = healthChecker.getStatus('python');
      assert.ok(status.lastCheck !== null);
    });

    it('should stop monitoring and clear interval', () => {
      healthChecker.start();
      assert.ok(healthChecker.intervalId !== null);

      healthChecker.stop();
      assert.strictEqual(healthChecker.intervalId, null);
    });

    it('should handle stop when not started', () => {
      // Should not throw
      assert.doesNotThrow(() => {
        healthChecker.stop();
      });
    });

    it('should perform periodic checks', async () => {
      // Mock successful response
      let callCount = 0;
      global.fetch = mock.fn(async () => {
        callCount++;
        return {
          ok: true,
          status: 200
        };
      });

      healthChecker.start();

      // Wait for multiple intervals
      await new Promise(resolve => setTimeout(resolve, 350));

      healthChecker.stop();

      // Should have been called multiple times (initial + periodic)
      // At 100ms interval over 350ms, we expect at least 3 checks
      assert.ok(callCount >= 4); // 2 backends * at least 2 checks
    });
  });

  describe('Edge Cases', () => {
    beforeEach(() => {
      healthChecker = new HealthChecker(mockBackends, 1000);
    });

    it('should handle unknown backend in checkBackend', async () => {
      // Should not throw
      await assert.doesNotReject(async () => {
        await healthChecker.checkBackend('unknown');
      });
    });

    it('should handle empty backends object', () => {
      const emptyChecker = new HealthChecker({}, 1000);
      const status = emptyChecker.getAllStatus();
      assert.deepStrictEqual(status, {});
    });

    it('should track response time accurately', async () => {
      // Mock response with slight delay
      global.fetch = mock.fn(async () => {
        await new Promise(resolve => setTimeout(resolve, 50));
        return {
          ok: true,
          status: 200
        };
      });

      await healthChecker.checkBackend('python');

      const status = healthChecker.getStatus('python');
      assert.ok(status.responseTime >= 50);
      assert.ok(status.responseTime < 200);
    });

    it('should update lastCheck timestamp', async () => {
      global.fetch = mock.fn(async () => ({
        ok: true,
        status: 200
      }));

      const beforeCheck = new Date();
      await healthChecker.checkBackend('python');
      const afterCheck = new Date();

      const status = healthChecker.getStatus('python');
      const lastCheckTime = new Date(status.lastCheck);

      assert.ok(lastCheckTime >= beforeCheck);
      assert.ok(lastCheckTime <= afterCheck);
    });
  });
});
