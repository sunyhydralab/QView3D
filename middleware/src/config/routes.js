/**
 * Simple proxy configuration
 *
 * The middleware acts as a pure reverse proxy, forwarding all requests to
 * whichever backend the user selected at startup (Python or JavaScript).
 *
 * No route-specific mapping - all routes go to the selected backend.
 * This allows the user to choose their preferred backend implementation
 * without the middleware making routing decisions.
 */

/**
 * Default backend for startup
 * User can change this via the /api/middleware/select-backend endpoint
 */
export const defaultBackend = 'python';

/**
 * Empty route map - all routes proxy to selected backend
 * Keeping this for backward compatibility with middleware code
 */
export const routeMap = {};
