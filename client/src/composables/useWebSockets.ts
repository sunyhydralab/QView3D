import { ref } from 'vue'
import {type Fabricator, fabricatorList} from '@/models/fabricator'
import {type Job} from "@/models/job";
// Use the shared socket from services instead of creating a duplicate connection
import { socket, onSocketEvent } from '@/services/socket';

// Keep track of cleanup functions for all socket listeners
const socketCleanupFunctions: (() => void)[] = [];

export function setupSockets() {
    // Clear any existing listeners first
    cleanupSockets();

    // Setup all socket listeners and store their cleanup functions
    socketCleanupFunctions.push(
        setupTempSocket(),
        setupStatusSocket(),
        setupQueueSocket(),
        setupErrorSocket(),
        setupCanPauseSocket(),
        setupPauseFeedbackSocket(),
        setupTimeStartedSocket(),
        setupTimeUpdateSocket(),
        setupProgressSocket(),
        setupReleaseSocket(),
        setupJobStatusSocket(),
        setupPortRepairSocket(),
        setupGCodeViewerSocket(),
        setupExtrusionSocket(),
        setupColorChangeBuffer(),
        setupMaxLayerHeightSocket(),
        setupCurrentLayerHeightSocket(),
        setupConsoleSocket()
    );
}

// Function to cleanup all socket listeners
export function cleanupSockets() {
    socketCleanupFunctions.forEach(cleanup => cleanup());
    socketCleanupFunctions.length = 0;
}

interface WebSocketDataPacket {
  fabricator_id?: string
  job_id?: string
  extruder_temp?: number
  bed_temp?: number
  status?: string
  queue?: Array<Job>
  error?: string
  canPause?: boolean
  file_pause?: boolean
  time_started?: number
  progress?: number
  released?: boolean
  Fabricator?: Record<string, any>
  gcode_num?: number
  level?: string
  message?: string
  extruded?: number
  colorbuff?: number
  max_layer_height?: number
  current_layer_height?: number
  elapsed?: number
  remaining?: number
  total?: number
  eta?: string
}

// *** PORTS ***
function setupTempSocket() {
  return onSocketEvent<WebSocketDataPacket>('temp_update', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        extruder_temp: data.extruder_temp,
        bed_temp: data.bed_temp
      };
    }
  });
}

// function to set up the socket for status updates
function setupStatusSocket() {
  return onSocketEvent<WebSocketDataPacket>('status_update', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        status: data.status
      };
    }
  });
}

function setupJobStatusSocket() {
  return onSocketEvent<WebSocketDataPacket>('job_status_update', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          status: data.status
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupQueueSocket() {
  return onSocketEvent<WebSocketDataPacket>('queue_update', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        queue: data.queue
      };
    }
  });
}

function setupErrorSocket() {
  return onSocketEvent<WebSocketDataPacket>('error_update', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        error: data.error
      };
    }
  });
}

function setupCanPauseSocket() {
  return onSocketEvent<WebSocketDataPacket>('can_pause', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        canPause: data.canPause
      };
    }
  });
}

// *** JOBS ***
function setupPauseFeedbackSocket() {
  return onSocketEvent<WebSocketDataPacket>('file_pause_update', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          file_pause: data.file_pause || false
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupTimeStartedSocket() {
  return onSocketEvent<WebSocketDataPacket>('set_time_started', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          time_started: data.time_started
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

// Helper function to format seconds as HH:MM:SS
function formatTime(seconds: number | undefined): string {
  if (seconds === undefined || seconds < 0) return 'Idle'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

// Helper function to format ETA timestamp as readable time
function formatETA(isoTimestamp: string | undefined): string {
  if (!isoTimestamp || isoTimestamp === 'Idle') return 'Idle'

  try {
    const etaDate = new Date(isoTimestamp)
    const now = new Date()

    // If ETA is in the past, return 'Soon'
    if (etaDate <= now) return 'Soon'

    // Format as time (e.g., "6:30 PM")
    return etaDate.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    })
  } catch (error) {
    console.error('Error formatting ETA:', error)
    return 'Unknown'
  }
}

// Function to update reactive time tracking for jobs
function setupTimeUpdateSocket() {
  return onSocketEvent<WebSocketDataPacket>('time_update', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        const job = printer.queue[jobIndex];

        // Initialize job_client if it doesn't exist
        const job_client = job.job_client || {
          elapsed_time: 'Idle',
          remaining_time: 'Idle',
          total_time: 'Idle',
          eta: 'Idle'
        };

        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...job,
          job_client: {
            ...job_client,
            elapsed_time: formatTime(data.elapsed),
            remaining_time: formatTime(data.remaining),
            total_time: formatTime(data.total),
            eta: formatETA(data.eta)
          },
          progress: data.progress !== undefined ? data.progress : job.progress
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };

        console.debug('Time update received:', {
          job_id: data.job_id,
          elapsed: updatedQueue[jobIndex].job_client?.elapsed_time,
          remaining: updatedQueue[jobIndex].job_client?.remaining_time,
          total: updatedQueue[jobIndex].job_client?.total_time,
          eta: updatedQueue[jobIndex].job_client?.eta,
          progress: updatedQueue[jobIndex].progress
        });
        break;
      }
    }
  });
}

// function to constantly update progress of job
function setupProgressSocket() {
  return onSocketEvent<WebSocketDataPacket>('progress_update', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue && data.progress !== undefined) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          progress: data.progress
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupReleaseSocket() {
  return onSocketEvent<WebSocketDataPacket>('release_job', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          released: data.released
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupPortRepairSocket() {
  return onSocketEvent<WebSocketDataPacket>('port_repair', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      console.log('printer Fabricator: ' + fabricatorList.value[index].device, ' data Fabricator: ' + data.Fabricator);
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        device: data.Fabricator || fabricatorList.value[index].device
      };
    } else {
      console.error('printer is undefined');
    }
  });
}

function setupGCodeViewerSocket() {
  return onSocketEvent<WebSocketDataPacket>('gcode_viewer', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          gcode_num: data.gcode_num
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

const arrayLevels = ['critical', 'error', 'warning', 'info', 'debug']
const colors = ['\x1b[95m', '\x1b[91m', '\x1b[93m', '\x1b[0m', '\x1b[94m']

function setupConsoleSocket() {
  // Initialize console arrays for all fabricators
  for (let i = 0; i < fabricatorList.value.length; i++) {
    if (fabricatorList.value[i].consoles) {
      const updatedConsoles = [...(fabricatorList.value[i].consoles || [])];
      for (let j = 0; j < 5; j++) {
        updatedConsoles[j] = [];
      }
      fabricatorList.value[i] = {
        ...fabricatorList.value[i],
        consoles: updatedConsoles
      };
    }
  }

  return onSocketEvent<WebSocketDataPacket>('console_update', (data) => {
    console.debug("console update", data);
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);

    if (index !== -1 && fabricatorList.value[index].consoles && data.level) {
      const maxLevelToAdd = arrayLevels.indexOf(data.level);

      if (maxLevelToAdd === -1) {
        console.error('Invalid console level:', data.level);
      } else {
        // Create a new consoles array to trigger reactivity
        const updatedConsoles = fabricatorList.value[index].consoles!.map((console, i) => {
          if (i >= maxLevelToAdd) {
            return [...console, colors[maxLevelToAdd] + data.message + '\x1b[0m'];
          }
          return console;
        });

        // Replace the entire object to trigger Vue reactivity
        fabricatorList.value[index] = {
          ...fabricatorList.value[index],
          consoles: updatedConsoles
        };
      }
    } else if (!data.level) {
      console.error('data.level is undefined');
    }
  });
}

function setupExtrusionSocket() {
  return onSocketEvent<WebSocketDataPacket>('extruded_update', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          extruded: data.extruded
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupColorChangeBuffer() {
  return onSocketEvent<WebSocketDataPacket>('color_buff', (data) => {
    const index = fabricatorList.value.findIndex((p: Fabricator) => p.id === data.fabricator_id);
    if (index !== -1) {
      // Replace the entire object to trigger Vue reactivity
      fabricatorList.value[index] = {
        ...fabricatorList.value[index],
        colorbuff: data.colorbuff
      };
    }
  });
}

function setupMaxLayerHeightSocket() {
  return onSocketEvent<WebSocketDataPacket>('max_layer_height', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          max_layer_height: data.max_layer_height
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}

function setupCurrentLayerHeightSocket() {
  return onSocketEvent<WebSocketDataPacket>('current_layer_height', (data) => {
    // Find printer and job index
    for (let i = 0; i < fabricatorList.value.length; i++) {
      const printer = fabricatorList.value[i];
      const jobIndex = printer.queue?.findIndex((job: Job) => job?.id === data.job_id) ?? -1;

      if (jobIndex !== -1 && printer.queue) {
        // Create new queue array with updated job to trigger reactivity
        const updatedQueue = [...printer.queue];
        updatedQueue[jobIndex] = {
          ...updatedQueue[jobIndex],
          current_layer_height: data.current_layer_height
        };

        // Replace entire printer object with updated queue
        fabricatorList.value[i] = {
          ...printer,
          queue: updatedQueue
        };
        break;
      }
    }
  });
}