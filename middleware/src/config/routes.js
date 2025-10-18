// Route-to-backend mapping for hybrid mode
export const routeMap = {
  // Serial operations - prefer JavaScript backend
  '/api/serial/*': 'javascript',
  '/api/gcode/*': 'javascript',

  // Database operations - Python backend only
  '/getjobs': 'python',
  '/getprinterinfo': 'python',
  '/register': 'python',
  '/deletefabricator': 'python',

  // Emulator operations - can use either
  '/startemulator': 'python',
  '/disconnectemulator': 'python',
  '/registeremulator': 'python',
  '/setemulatortemperature': 'python',
  '/runemulatortest': 'python',
  '/resetemulator': 'python',

  // Job management - Python backend
  '/addjobtoqueue': 'python',
  '/autoqueue': 'python',
  '/cancelfromqueue': 'python',
  '/startprint': 'python',
  '/releasejob': 'python',

  // Port operations
  '/getports': 'python',
  '/setstatus': 'python'
};

export const defaultBackend = 'python';
