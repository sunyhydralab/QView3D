/**
 * Logger utility for QView3D client
 * Provides structured logging with environment awareness
 * In production, logs are suppressed or sent to monitoring service
 */

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3,
  NONE = 4
}

class Logger {
  private isDevelopment = import.meta.env.DEV;
  private logLevel: LogLevel = this.isDevelopment ? LogLevel.DEBUG : LogLevel.WARN;
  private logHistory: Array<{ level: LogLevel; message: string; data?: any; timestamp: Date }> = [];
  private maxHistorySize = 100;

  /**
   * Set the minimum log level
   */
  setLogLevel(level: LogLevel) {
    this.logLevel = level;
  }

  /**
   * Get recent log history (useful for debugging)
   */
  getHistory() {
    return [...this.logHistory];
  }

  /**
   * Clear log history
   */
  clearHistory() {
    this.logHistory = [];
  }

  private shouldLog(level: LogLevel): boolean {
    return level >= this.logLevel;
  }

  private addToHistory(level: LogLevel, message: string, data?: any) {
    this.logHistory.push({
      level,
      message,
      data,
      timestamp: new Date()
    });

    // Keep history size manageable
    if (this.logHistory.length > this.maxHistorySize) {
      this.logHistory.shift();
    }
  }

  private formatMessage(level: string, message: string): string {
    const timestamp = new Date().toISOString();
    return `[${timestamp}] [${level}] ${message}`;
  }

  debug(message: string, data?: any) {
    if (this.shouldLog(LogLevel.DEBUG)) {
      this.addToHistory(LogLevel.DEBUG, message, data);
      if (this.isDevelopment) {
        console.log(this.formatMessage('DEBUG', message), data || '');
      }
    }
  }

  info(message: string, data?: any) {
    if (this.shouldLog(LogLevel.INFO)) {
      this.addToHistory(LogLevel.INFO, message, data);
      if (this.isDevelopment) {
        console.log(this.formatMessage('INFO', message), data || '');
      }
      // In production, could send to monitoring service
    }
  }

  warn(message: string, data?: any) {
    if (this.shouldLog(LogLevel.WARN)) {
      this.addToHistory(LogLevel.WARN, message, data);
      console.warn(this.formatMessage('WARN', message), data || '');
      // In production, send to monitoring service
    }
  }

  error(message: string, error?: any) {
    if (this.shouldLog(LogLevel.ERROR)) {
      this.addToHistory(LogLevel.ERROR, message, error);
      console.error(this.formatMessage('ERROR', message), error || '');

      // In production, send to error tracking service
      if (!this.isDevelopment && typeof window !== 'undefined') {
        // Example: Send to error tracking service
        // window.errorTracker?.captureException(error, { message });
      }
    }
  }

  /**
   * Group related log messages
   */
  group(label: string) {
    if (this.isDevelopment && this.shouldLog(LogLevel.DEBUG)) {
      console.group(label);
    }
  }

  groupEnd() {
    if (this.isDevelopment && this.shouldLog(LogLevel.DEBUG)) {
      console.groupEnd();
    }
  }

  /**
   * Time performance measurements
   */
  time(label: string) {
    if (this.isDevelopment && this.shouldLog(LogLevel.DEBUG)) {
      console.time(label);
    }
  }

  timeEnd(label: string) {
    if (this.isDevelopment && this.shouldLog(LogLevel.DEBUG)) {
      console.timeEnd(label);
    }
  }

  /**
   * Table display for structured data
   */
  table(data: any) {
    if (this.isDevelopment && this.shouldLog(LogLevel.DEBUG)) {
      console.table(data);
    }
  }
}

// Export singleton instance
export const logger = new Logger();

// Export LogLevel for external use
export default logger;