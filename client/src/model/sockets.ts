import { socket } from './myFetch'
import type { Device } from './ports'
import { jobTime } from './jobs'

// *** PORTS ***
export function setupTempSocket(printers: any) {
  socket.value.on('temp_update', (data: any) => {
    const printer = printers.value.find((p: Device) => p.id === data.printerid)
    if (printer) {
      printer.extruder_temp = data.extruder_temp
      printer.bed_temp = data.bed_temp
    }
  })
}

// function to set up the socket for status updates
export function setupStatusSocket(printers: any) {
  socket.value.on('status_update', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.fabricator_id)
      if (printer) {
        printer.status = data.status
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupQueueSocket(printers: any) {
  socket.value.on('queue_update', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.queue = data.queue
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupErrorSocket(printers: any) {
  socket.value.on('error_update', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      console.log(printer)
      if (printer) {
        printer.error = data.error
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupCanPauseSocket(printers: any) {
  socket.value.on('can_pause', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.canPause = data.canPause
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
  console.log('queue socket set up')
}

// *** JOBS ***
export function setupPauseFeedbackSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('file_pause_update', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.file_pause = data.file_pause
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupTimeStartedSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('set_time_started', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.time_started = data.time_started
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

// function to constantly update progress of job
export function setupProgressSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('progress_update', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.progress = data.progress
        // job.elapsed_time = data.elapsed_time
        // Update the display value only if progress is defined
        if (data.progress !== undefined) {
          job.progress = data.progress
        }
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupReleaseSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('release_job', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)
      if (job) {
        job.released = data.released
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupJobStatusSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('job_status_update', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.status = data.status
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupPortRepairSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.value.on('port_repair', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.printer_id)
      console.log('printer device: ' + printer.device, ' data device: ' + data.device)
      printer.device = data.device
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupGCodeViewerSocket(printers: any) {
  socket.value.on('gcode_viewer', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.gcode_num = data.gcode_num
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupExtrusionSocket(printers: any) {
  socket.value.on('extruded_update', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.extruded = data.extruded
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupColorChangeBuffer(printers: any) {
  socket.value.on('color_buff', (data: any) => {
    if (printers) {
      const printer = printers.value.find((p: Device) => p.id === data.printerid)
      if (printer) {
        printer.colorbuff = data.colorbuff
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupMaxLayerHeightSocket(printers: any) {
  socket.value.on('max_layer_height', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.max_layer_height = data.max_layer_height
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}

export function setupCurrentLayerHeightSocket(printers: any) {
  socket.value.on('current_layer_height', (data: any) => {
    if (printers) {
      const job = printers.value
        .flatMap((printer: { queue: any }) => printer.queue)
        .find((job: { id: any }) => job?.id === data.job_id)

      if (job) {
        job.current_layer_height = data.current_layer_height
      }
    } else {
      console.error('printers or printers.value is undefined')
    }
  })
}