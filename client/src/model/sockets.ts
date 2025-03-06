import { socket } from './myFetch'
import {type Device} from './ports'
import {type Job} from "@/model/jobs";

export function setupSockets(printers: Array<Device>) {
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
    setupGCodeLineSocket(printers)
    setupExtrusionSocket(printers)
    setupColorChangeBuffer(printers)
    setupMaxLayerHeightSocket(printers)
    setupCurrentLayerHeightSocket(printers)
    setupConsoleSocket(printers)
}

// *** PORTS ***
export function setupTempSocket(printers: Array<Device>) {
  socket.value.off('temp_update')
  socket.value.on('temp_update', (data: any) => {
    const printer = printers.find((p: Device) => p.id === data.printerid)
    if (printer) {
      printer.extruder_temp = data.extruder_temp
      printer.bed_temp = data.bed_temp
    }
  })
}

// function to set up the socket for status updates
export function setupStatusSocket(printers: Array<Device>) {
  socket.value.off('status_update')
  socket.value.on('status_update', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.fabricator_id)
      if (printer) {
        printer.status = data.status
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupJobStatusSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('job_status_update')
  socket.value.on('job_status_update', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.status = data.status
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupQueueSocket(printers: Array<Device>) {
  socket.value.off('queue_update')
  socket.value.on('queue_update', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.queue = data.queue
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupErrorSocket(printers: Array<Device>) {
  socket.value.off('error_update')
  socket.value.on('error_update', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.error = data.error
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupCanPauseSocket(printers: Array<Device>) {
  socket.value.off('can_pause')
  socket.value.on('can_pause', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.canPause = data.canPause
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

// *** JOBS ***
export function setupPauseFeedbackSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('file_pause_update')
  socket.value.on('file_pause_update', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.file_pause = data.file_pause
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupTimeStartedSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('set_time_started')
  socket.value.on('set_time_started', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
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
export function setupProgressSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('progress_update')
  socket.value.on('progress_update', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
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

export function setupReleaseSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('release_job')
  socket.value.on('release_job', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)
      if (job) {
        job.released = data.released
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupPortRepairSocket(printers: Array<Device>) {
  // Always set up the socket connection and event listener
  socket.value.off('port_repair')
  socket.value.on('port_repair', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printer_id)
      if (printer) {
        console.log('printer device: ' + printer.device, ' data device: ' + data.device)
        printer.device = data.device
      } else{
        console.error('printer is undefined')
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupGCodeViewerSocket(printers: Array<Device>) {
  socket.value.off('gcode_viewer')
  socket.value.on('gcode_viewer', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.gcode_num = data.gcode_num
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupGCodeLineSocket(printers: Array<Device>) {
  for (let i = 0; i < printers.length; i++) {
    printers[i].gcodeLines = []
  }
  socket.value.off('gcode_line')
  socket.value.on('gcode_line', (data: any) => {
    if (printers) {
      const printer: Device | undefined = printers.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.gcodeLines!.push(data.line)
      } else {
        console.error('printer is undefined')
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

const arrayLevels = ['critical', 'error', 'warning', 'info', 'debug']
const colors = ['\x1b[95m', '\x1b[91m', '\x1b[93m', '\x1b[0m', '\x1b[94m']

export function setupConsoleSocket(printers: Array<Device>) {
  for (let i = 0; i < printers.length; i++) {
    printers[i].gcodeLines = []
  }
  socket.value.off('console_update')
  socket.value.on('console_update', (data: any) => {
    console.debug("console update", data)
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printerid)
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
          if (data.level === 'info') printer.gcodeLines!.push(data.message.split(':')[0]);

        } else {
          console.error('data.level is undefined')
        }
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupExtrusionSocket(printers: Array<Device>) {
  socket.value.off('extruded_update')
  socket.value.on('extruded_update', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.extruded = data.extruded
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupColorChangeBuffer(printers: Array<Device>) {
  socket.value.off('color_buff')
  socket.value.on('color_buff', (data: any) => {
    if (printers) {
      const printer = printers.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.colorbuff = data.colorbuff
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupMaxLayerHeightSocket(printers: Array<Device>) {
  socket.value.off('max_layer_height')
  socket.value.on('max_layer_height', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.max_layer_height = data.max_layer_height
      }
    } else {
      console.error('printers is undefined')
    }
  })
}

export function setupCurrentLayerHeightSocket(printers: Array<Device>) {
  socket.value.off('current_layer_height')
  socket.value.on('current_layer_height', (data: any) => {
    if (printers) {
      const job = printers
        .flatMap((printer: Device) => printer.queue)
        .find((job: Job | undefined) => job?.id === data.job_id)

      if (job) {
        job.current_layer_height = data.current_layer_height
      }
    } else {
      console.error('printers is undefined')
    }
  })
}