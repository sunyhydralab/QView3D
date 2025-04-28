import { API_URL } from '@/composables/useIPSettings'
import io from 'socket.io-client'
import { ref } from 'vue'
import {type Fabricator} from '@/models/fabricator'
import {type Job} from "@/models/job";

export const socket = ref(io(API_URL.value, {
    transports: ['websocket']
}));

export function setupSockets(printers: Array<Fabricator>) {
    setupTempSocket(printers)
    setupStatusSocket(printers)
    setupQueueSocket(printers)
    setupErrorSocket(printers)
    setupCanPauseSocket(printers)
    setupPauseFeedbackSocket(printers)
    setupTimeStartedSocket(printers)
    setupProgressSocket(printers)
    setupReleaseSocket(printers)
    setupJobStatusSocket(printers)
    setupPortRepairSocket(printers)
    setupGCodeViewerSocket(printers)
    setupExtrusionSocket(printers)
    setupColorChangeBuffer(printers)
    setupMaxLayerHeightSocket(printers)
    setupCurrentLayerHeightSocket(printers)
    setupConsoleSocket(printers)
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
}

// *** PORTS ***
function setupTempSocket(printers: Array<Fabricator>) {
  socket.value.off('temp_update')
  socket.value.on('temp_update', (data: WebSocketDataPacket) => {
    const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.extruder_temp = data.extruder_temp
      printer.bed_temp = data.bed_temp
    }
    console.debug()
  })
}

// function to set up the socket for status updates
function setupStatusSocket(printers: Array<Fabricator>) {
  socket.value.off('status_update')
  socket.value.on('status_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        printer.status = data.status
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupJobStatusSocket(printers: Array<Fabricator>) {
  socket.value.off('job_status_update')
  // Always set up the socket connection and event listener
  socket.value.off('job_status_update')
  socket.value.on('job_status_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.status = data.status
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupQueueSocket(printers: Array<Fabricator>) {
  socket.value.off('queue_update')
  socket.value.on('queue_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        printer.queue = data.queue
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupErrorSocket(printers: Array<Fabricator>) {
  socket.value.off('error_update')
  socket.value.on('error_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        printer.error = data.error
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupCanPauseSocket(printers: Array<Fabricator>) {
  socket.value.off('can_pause')
  socket.value.on('can_pause', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        printer.canPause = data.canPause
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

// *** JOBS ***
function setupPauseFeedbackSocket(printers: Array<Fabricator>) {
  socket.value.off('file_pause_update')
  socket.value.on('file_pause_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.file_pause = data.file_pause || false
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupTimeStartedSocket(printers: Array<Fabricator>) {
  socket.value.off('set_time_started')
  // Always set up the socket connection and event listener
  socket.value.off('set_time_started')
  socket.value.on('set_time_started', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.time_started = data.time_started
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

// function to constantly update progress of job
function setupProgressSocket(printers: Array<Fabricator>) {
  socket.value.off('progress_update')
  // Always set up the socket connection and event listener
  socket.value.off('progress_update')
  socket.value.on('progress_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.progress = data.progress
        // job.elapsed_time = data.elapsed_time
        // Update the display value only if progress is defined
        if (data.progress !== undefined) {
          job.progress = data.progress
        }
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupReleaseSocket(printers: Array<Fabricator>) {
  socket.value.off('release_job')
  // Always set up the socket connection and event listener
  socket.value.off('release_job')
  socket.value.on('release_job', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)
      if (job) {
        job.released = data.released
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupPortRepairSocket(printers: Array<Fabricator>) {
    socket.value.off('port_repair')
  // Always set up the socket connection and event listener
  socket.value.off('port_repair')
  socket.value.on('port_repair', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        console.log('printer Fabricator: ' + printer.device, ' data Fabricator: ' + data.Fabricator)
        printer.device = data.Fabricator || printer.device
      } else{
        console.error('printer is undefined')
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupGCodeViewerSocket(printers: Array<Fabricator>) {
  socket.value.off('gcode_viewer')
  socket.value.on('gcode_viewer', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.gcode_num = data.gcode_num
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

const arrayLevels = ['critical', 'error', 'warning', 'info', 'debug']
const colors = ['\x1b[95m', '\x1b[91m', '\x1b[93m', '\x1b[0m', '\x1b[94m']

function setupConsoleSocket(printers: Array<Fabricator>) {
  for (let i = 0; i < printers.length; i++) {
    if (printers[i].consoles) {
      for (let j = 0; j < 5; j++) {
        printers[i].consoles![j] = []
      }
    }
  }
  socket.value.off('console_update')
  socket.value.on('console_update', (data: WebSocketDataPacket) => {
    console.debug("console update", data)
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer && printer.consoles) {
        if (data.level) {
          const maxLevelToAdd = arrayLevels.indexOf(data.level)
          if (maxLevelToAdd === -1) {
            console.error('Invalid console level:', data.level)
          } else {
            for (let i = maxLevelToAdd; i < printer.consoles.length; i++) {
              printer.consoles[i].push(colors[maxLevelToAdd] + data.message + '\x1b[0m')
            }
          }

        } else {
          console.error('data.level is undefined')
        }
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupExtrusionSocket(printers: Array<Fabricator>) {
  socket.value.off('extruded_update')
  socket.value.on('extruded_update', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.extruded = data.extruded
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupColorChangeBuffer(printers: Array<Fabricator>) {
  socket.value.off('color_buff')
  socket.value.on('color_buff', (data: WebSocketDataPacket) => {
    if (printers) {
      const printer = printers.find((p: Fabricator) => p.id === data.fabricator_id)
      if (printer) {
        printer.colorbuff = data.colorbuff
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupMaxLayerHeightSocket(printers: Array<Fabricator>) {
  socket.value.off('max_layer_height')
  socket.value.on('max_layer_height', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.max_layer_height = data.max_layer_height
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

function setupCurrentLayerHeightSocket(printers: Array<Fabricator>) {
  socket.value.off('current_layer_height')
  socket.value.on('current_layer_height', (data: WebSocketDataPacket) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Fabricator) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.current_layer_height = data.current_layer_height
      }
    } else {
      console.error('printers is undefined')
    }
  })
}