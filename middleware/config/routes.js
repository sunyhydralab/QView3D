/**
 * Route Mapping Configuration
 * Maps specific routes to backends for intelligent routing
 */

/**
 * Route map: Define which backend handles which routes
 * - 'python': Route to Python backend
 * - 'javascript': Route to JavaScript backend
 * - 'either': Can be handled by either backend (uses active backend)
 */
export const routeMap = {
  // Emulator routes - Python backend
  '/api/emulator/create': 'python',
  '/api/emulator/list': 'python',
  '/api/emulator/delete': 'python',
  '/api/emulator/update_status': 'python',
  '/startemulator': 'python',
  '/registeremulator': 'python',
  '/disconnectemulator': 'python',

  // Serial/Port detection - Can use either backend
  '/getports': 'either',
  '/checkport': 'either',
  '/getfabricators': 'either',
  '/register': 'either',
  '/deletefabricator': 'either',

  // Job management - Can use either backend
  '/getjobs': 'either',
  '/addjobtoqueue': 'either',
  '/autoqueue': 'either',
  '/deletejob': 'either',
  '/cancelfromqueue': 'either',
  '/reorderqueue': 'either',  // New frontend-friendly route
  '/movejob': 'either',  // Legacy route
  '/bumpjob': 'either',
  '/startprint': 'either',
  '/releasejob': 'either',

  // Printer status and control - Can use either backend
  '/getprinterinfo': 'either',
  '/getprinters': 'either',
  '/setstatus': 'either',
  '/pausequeue': 'either',
  '/resumequeue': 'either',
  '/cancelqueue': 'either',
  '/restartqueue': 'either',

  // Issues - Can use either backend
  '/getissues': 'either',
  '/createissue': 'either',
  '/updateissue': 'either',  // New route
  '/deleteissue': 'either',
  '/resolveissue': 'either',  // New route
  '/editissue': 'either',  // Legacy route

  // Fabricator models - Can use either backend
  '/api/fabricators/models': 'either',

  // WebSocket/SocketIO - Route to active backend
  '/socket.io': 'either'
};

/**
 * Default backend for unmapped routes
 */
export const defaultBackend = 'python';
