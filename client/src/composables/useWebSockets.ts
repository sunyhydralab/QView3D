import { API_URL } from '@/composables/useIPSettings'
import io from 'socket.io-client'
import { ref } from 'vue'
import {type Fabricator, fabricatorList} from '@/models/fabricator'
import {type Job} from "@/models/job";

export const socket = ref(io(API_URL.value, {
    transports: ['websocket']
}));

export function setupSockets() {
    setupTempSocket()
    setupStatusSocket()
    setupQueueSocket()
    setupErrorSocket()
    setupCanPauseSocket()
    setupPauseFeedbackSocket()
    setupTimeStartedSocket()
    setupTimeUpdateSocket()
    setupProgressSocket()
    setupReleaseSocket()
    setupJobStatusSocket()
    setupPortRepairSocket()
    setupGCodeViewerSocket()
    setupExtrusionSocket()
    setupColorChangeBuffer()
    setupMaxLayerHeightSocket()
    setupCurrentLayerHeightSocket()
    setupConsoleSocket()
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
  socket.value.off('temp_update')
  socket.value.on('temp_update', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.extruder_temp = data.extruder_temp
      printer.bed_temp = data.bed_temp
    }
    console.debug()
  })
}

// function to set up the socket for status updates
function setupStatusSocket() {
  socket.value.off('status_update')
  socket.value.on('status_update', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.status = data.status
    }
  })
}

function setupJobStatusSocket() {
  socket.value.off('job_status_update')
  socket.value.on('job_status_update', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.status = data.status
    }
  })
}

function setupQueueSocket() {
  socket.value.off('queue_update')
  socket.value.on('queue_update', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.queue = data.queue
    }
  })
}

function setupErrorSocket() {
  socket.value.off('error_update')
  socket.value.on('error_update', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.error = data.error
    }
  })
}

function setupCanPauseSocket() {
  socket.value.off('can_pause')
  socket.value.on('can_pause', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.canPause = data.canPause
    }
  })
}

// *** JOBS ***
function setupPauseFeedbackSocket() {
  socket.value.off('file_pause_update')
  socket.value.on('file_pause_update', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.file_pause = data.file_pause || false
    }
  })
}

function setupTimeStartedSocket() {
  socket.value.off('set_time_started')
  socket.value.on('set_time_started', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.time_started = data.time_started
    }
  })
}

// Helper function to format seconds as HH:MM:SS
function formatTime(seconds: number | undefined): string {
  if (seconds === undefined || seconds < 0) return 'Idle'

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)

  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

// Function to update reactive time tracking for jobs
function setupTimeUpdateSocket() {
  socket.value.off('time_update')
  socket.value.on('time_update', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      // Initialize job_client if it doesn't exist
      if (!job.job_client) {
        job.job_client = {
          elapsed_time: 'Idle',
          remaining_time: 'Idle',
          total_time: 'Idle',
          eta: 'Idle'
        }
      }

      // Update time fields with formatted values
      job.job_client.elapsed_time = formatTime(data.elapsed)
      job.job_client.remaining_time = formatTime(data.remaining)
      job.job_client.total_time = formatTime(data.total)
      job.job_client.eta = data.eta || 'Idle'

      // Also update progress if provided
      if (data.progress !== undefined) {
        job.progress = data.progress
      }

      console.debug('Time update received:', {
        job_id: data.job_id,
        elapsed: job.job_client.elapsed_time,
        remaining: job.job_client.remaining_time,
        total: job.job_client.total_time,
        eta: job.job_client.eta,
        progress: job.progress
      })
    }
  })
}

// function to constantly update progress of job
function setupProgressSocket() {
  socket.value.off('progress_update')
  socket.value.on('progress_update', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
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
  })
}

function setupReleaseSocket() {
  socket.value.off('release_job')
  socket.value.on('release_job', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)
    if (job) {
      job.released = data.released
    }
  })
}

function setupPortRepairSocket() {
  socket.value.off('port_repair')
  socket.value.on('port_repair', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      console.log('printer Fabricator: ' + printer.device, ' data Fabricator: ' + data.Fabricator)
      printer.device = data.Fabricator || printer.device
    } else{
      console.error('printer is undefined')
    }
  })
}

function setupGCodeViewerSocket() {
  socket.value.off('gcode_viewer')
  socket.value.on('gcode_viewer', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.gcode_num = data.gcode_num
    }
  })
}

const arrayLevels = ['critical', 'error', 'warning', 'info', 'debug']
const colors = ['\x1b[95m', '\x1b[91m', '\x1b[93m', '\x1b[0m', '\x1b[94m']

function setupConsoleSocket() {
  for (let i = 0; i < fabricatorList.value.length; i++) {
    if (fabricatorList.value[i].consoles) {
      for (let j = 0; j < 5; j++) {
        fabricatorList.value[i].consoles![j] = []
      }
    }
  }
  socket.value.off('console_update')
  socket.value.on('console_update', (data: WebSocketDataPacket) => {
    console.debug("console update", data)
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
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
  })
}

function setupExtrusionSocket() {
  socket.value.off('extruded_update')
  socket.value.on('extruded_update', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.extruded = data.extruded
    }
  })
}

function setupColorChangeBuffer() {
  socket.value.off('color_buff')
  socket.value.on('color_buff', (data: WebSocketDataPacket) => {
    const printer = fabricatorList.value.find((p: Fabricator) => p.id === data.fabricator_id)
    if (printer) {
      printer.colorbuff = data.colorbuff
    }
  })
}

function setupMaxLayerHeightSocket() {
  socket.value.off('max_layer_height')
  socket.value.on('max_layer_height', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.max_layer_height = data.max_layer_height
    }
  })
}

function setupCurrentLayerHeightSocket() {
  socket.value.off('current_layer_height')
  socket.value.on('current_layer_height', (data: WebSocketDataPacket) => {
    const job = fabricatorList.value
      .flatMap((printer: Fabricator) => printer.queue)
      .find((job: Job | undefined) => job?.id === data.job_id)

    if (job) {
      job.current_layer_height = data.current_layer_height
    }
  })
}