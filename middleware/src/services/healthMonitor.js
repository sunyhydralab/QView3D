import axios from 'axios';
import logger from '../utils/logger.js';

export class HealthMonitor {
  constructor(backends) {
    this.backends = backends;
    this.healthStatus = {};
    this.checkInterval = 5000; // 5 seconds
    this.intervalId = null;

    // Initialize health status
    Object.keys(backends).forEach(key => {
      this.healthStatus[key] = {
        isHealthy: false,
        lastCheck: null,
        error: null
      };
    });
  }

  async checkBackendHealth(name, backend) {
    try {
      const response = await axios.get(
        `${backend.url}${backend.healthEndpoint}`,
        { timeout: 3000 }
      );

      this.healthStatus[name] = {
        isHealthy: response.status === 200,
        lastCheck: new Date(),
        error: null
      };

      return true;
    } catch (error) {
      this.healthStatus[name] = {
        isHealthy: false,
        lastCheck: new Date(),
        error: error.message
      };

      logger.warn(`Backend ${name} health check failed: ${error.message}`);
      return false;
    }
  }

  async checkAllBackends() {
    const checks = Object.entries(this.backends).map(([name, backend]) =>
      this.checkBackendHealth(name, backend)
    );

    await Promise.all(checks);
  }

  startMonitoring() {
    // Initial check
    this.checkAllBackends();

    // Periodic checks
    this.intervalId = setInterval(() => {
      this.checkAllBackends();
    }, this.checkInterval);

    logger.info('Health monitoring started');
  }

  stopMonitoring() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      logger.info('Health monitoring stopped');
    }
  }

  getStatus() {
    return this.healthStatus;
  }

  isBackendHealthy(name) {
    return this.healthStatus[name]?.isHealthy || false;
  }
}
