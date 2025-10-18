import logger from './logger.js';

export class AppError extends Error {
  constructor(message, statusCode = 500, details = {}) {
    super(message);
    this.statusCode = statusCode;
    this.details = details;
    this.isOperational = true;
    Error.captureStackTrace(this, this.constructor);
  }
}

export function handleError(err, req, res, next) {
  const { statusCode = 500, message, details } = err;

  logger.error(`Error: ${message}`, {
    statusCode,
    details,
    path: req.path,
    method: req.method
  });

  // Don't leak error details in production
  const response = {
    error: message,
    ...(process.env.NODE_ENV === 'development' && { details, stack: err.stack })
  };

  res.status(statusCode).json(response);
}

export function asyncHandler(fn) {
  return (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
