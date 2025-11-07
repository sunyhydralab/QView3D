/**
 * Backend Health Monitoring System
 *
 * Monitors the health status of both Python and JavaScript backends
 * with periodic checks, response time tracking, and status management.
 */

/**
 * Health status constants
 */
const HealthStatus = {
  HEALTHY: 'healthy',
  UNHEALTHY: 'unhealthy',
  DOWN: 'down'
};

/**
 * HealthChecker class for monitoring backend services
 */
export class HealthChecker {
  constructor(backends, interval = 10000) {
    this.backends = backends;
    this.interval = interval;
    this.status = {};
    this.intervalId = null;
    this.timeout = 5000; // 5 second timeout for health checks

    // Initialize status for each backend
    Object.keys(backends).forEach(name => {
      // JavaScript backend is disabled for now
      if (name === 'javascript') {
        this.status[name] = {
          status: 'disabled',
          responseTime: null,
          lastCheck: null,
          lastError: 'Backend temporarily disabled',
          consecutiveFailures: 0
        };
      } else {
        this.status[name] = {
          status: HealthStatus.HEALTHY,
          responseTime: null,
          lastCheck: null,
          lastError: null,
          consecutiveFailures: 0
        };
      }
    });
  }

  /**
   * Start automatic health monitoring
   */
  start() {
    console.log('[HealthChecker] Starting health monitoring...');
    console.log(`[HealthChecker] Check interval: ${this.interval}ms`);
    console.log(`[HealthChecker] Request timeout: ${this.timeout}ms`);

    // Run initial check immediately
    this.checkAll();

    // Schedule periodic checks
    this.intervalId = setInterval(() => {
      this.checkAll();
    }, this.interval);
  }

  /**
   * Stop automatic health monitoring
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('[HealthChecker] Health monitoring stopped');
    }
  }

  /**
   * Check health of all backends
   */
  async checkAll() {
    // Skip JavaScript backend health checks for now
    const backendsToCheck = Object.keys(this.backends).filter(name => name !== 'javascript');
    const checks = backendsToCheck.map(name =>
      this.checkBackend(name)
    );
    await Promise.all(checks);
  }

  /**
   * Check health of a specific backend
   * @param {string} name - Backend name (python/javascript)
   */
  async checkBackend(name) {
    const backend = this.backends[name];
    if (!backend) {
      console.error(`[HealthChecker] Unknown backend: ${name}`);
      return;
    }

    const startTime = Date.now();
    const url = `${backend.url}${backend.healthEndpoint}`;

    try {
      // Fetch with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        method: 'GET',
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      const responseTime = Date.now() - startTime;
      const isHealthy = response.ok;

      if (isHealthy) {
        // Backend is healthy
        const previousStatus = this.status[name].status;
        this.status[name] = {
          status: HealthStatus.HEALTHY,
          responseTime,
          lastCheck: new Date().toISOString(),
          lastError: null,
          consecutiveFailures: 0
        };

        // Log recovery if backend was previously down
        if (previousStatus !== HealthStatus.HEALTHY) {
          console.log(`[HealthChecker] ${name} backend recovered (${responseTime}ms)`);
        }
      } else {
        // Backend responded but not healthy
        this.handleUnhealthyResponse(name, responseTime, `HTTP ${response.status}`);
      }
    } catch (error) {
      // Backend is down or unreachable
      this.handleFailure(name, error);
    }
  }

  /**
   * Handle unhealthy backend response
   */
  handleUnhealthyResponse(name, responseTime, reason) {
    const previousStatus = this.status[name].status;
    this.status[name].consecutiveFailures++;

    const newStatus = this.status[name].consecutiveFailures >= 3
      ? HealthStatus.DOWN
      : HealthStatus.UNHEALTHY;

    this.status[name] = {
      ...this.status[name],
      status: newStatus,
      responseTime,
      lastCheck: new Date().toISOString(),
      lastError: reason
    };

    if (previousStatus !== newStatus) {
      console.warn(`[HealthChecker] ${name} backend ${newStatus}: ${reason}`);
    }
  }

  /**
   * Handle backend check failure
   */
  handleFailure(name, error) {
    const previousStatus = this.status[name].status;
    this.status[name].consecutiveFailures++;

    const errorMessage = error.name === 'AbortError'
      ? 'Request timeout'
      : error.message;

    const newStatus = this.status[name].consecutiveFailures >= 3
      ? HealthStatus.DOWN
      : HealthStatus.UNHEALTHY;

    this.status[name] = {
      ...this.status[name],
      status: newStatus,
      responseTime: null,
      lastCheck: new Date().toISOString(),
      lastError: errorMessage
    };

    if (previousStatus !== newStatus) {
      console.warn(`[HealthChecker] ${name} backend ${newStatus}: ${errorMessage}`);
    }
  }

  /**
   * Get status of a specific backend
   * @param {string} name - Backend name
   * @returns {Object} Status object
   */
  getStatus(name) {
    return this.status[name] || null;
  }

  /**
   * Get status of all backends
   * @returns {Object} All backend statuses
   */
  getAllStatus() {
    return { ...this.status };
  }

  /**
   * Check if a backend is healthy
   * @param {string} name - Backend name
   * @returns {boolean}
   */
  isHealthy(name) {
    return this.status[name]?.status === HealthStatus.HEALTHY;
  }

  /**
   * Check if a backend is down
   * @param {string} name - Backend name
   * @returns {boolean}
   */
  isDown(name) {
    return this.status[name]?.status === HealthStatus.DOWN;
  }
}

export default HealthChecker;
