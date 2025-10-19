// Route-to-backend mapping for hybrid mode
export const routeMap = {
  // Serial operations - prefer JavaScript backend
  '/api/serial': 'javascript',
  '/api/gcode': 'javascript',
  '/api/printers': 'javascript',

  // Database operations - both backends support now
  '/getjobs': 'either',
  '/getfabricators': 'either',
  '/getissues': 'either',
  '/getfavoritejobs': 'either',

  // Fabricator/Printer operations - both backends
  '/getports': 'either',
  '/register': 'either',
  '/deletefabricator': 'either',
  '/editname': 'either',
  '/setstatus': 'either',
  '/movefabricatorlist': 'either',
  '/getfabricatorbyid': 'either',

  // Job management - both backends
  '/addjobtoqueue': 'either',
  '/autoqueue': 'either',
  '/canceljob': 'either',
  '/cancelfromqueue': 'either',
  '/updatejobstatus': 'either',
  '/deletejob': 'either',
  '/startprint': 'either',
  '/releasejob': 'python',
  '/rerunjob': 'python',
  '/bumpjob': 'python',
  '/movejob': 'python',
  '/getfile': 'either',
  '/favoritejob': 'either',
  '/assignissue': 'either',
  '/removeissue': 'either',
  '/savecomment': 'either',

  // Issue operations - both backends
  '/createissue': 'either',
  '/updateissue': 'either',
  '/deleteissue': 'either',
  '/getissue': 'either',
  '/getissuesbycategory': 'either',
  '/resolveissue': 'either',

  // Emulator operations - Python only
  '/startemulator': 'python',
  '/disconnectemulator': 'python',
  '/registeremulator': 'python',
  '/setemulatortemperature': 'python',
  '/runemulatortest': 'python',
  '/resetemulator': 'python',

  // Python-specific operations
  '/diagnose': 'python',
  '/repair': 'python',
  '/movehead': 'python',
  '/downloadcsv': 'python',
  '/removeCSV': 'python',
  '/repairports': 'python',
  '/refetchtimedata': 'python',
  '/clearspace': 'python',
  '/nullifyjobs': 'python',
  '/jobdbinsert': 'python'
};

export const defaultBackend = 'python';
