// ts file to retrieve job information
import { useRouter } from 'vue-router'
import { api } from './ports'
import { toast } from './toast'
import { type Device } from '@/model/ports'
import { onUnmounted, ref } from 'vue'
import { socket } from './myFetch'
import { saveAs } from 'file-saver'

export interface Job {
  id: number
  name: string
  file: File
  download_link?: string
  file_name_original: string
  date?: Date
  status?: string
  progress?: number //store progress of job
  printer: string //store printer name
  printerid: number
  file_pause: number 
  priority?: string
  released: number 
  total_time?: number
  elapsed_time?: number
  remaining_time?: number
  timer?: NodeJS.Timeout
}

export function useGetJobs() {
  return {
    async jobhistory(page: number, pageSize: number, printerIds?: number[], oldestFirst?: boolean) {
      try {
        const response = await api(
          `getjobs?page=${page}&pageSize=${pageSize}&printerIds=${JSON.stringify(printerIds)}&oldestFirst=${oldestFirst}`
        )
        return response
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the jobs')
      }
    }
  }
}

export function useAddJobToQueue() {
  return {
    async addJobToQueue(job: FormData) {
      try {
        const response = await api('addjobtoqueue', job)
        if (response) {
          return response
        } else {
          console.error('Response is undefined or null')
          return { success: false, message: 'Response is undefined or null.' }
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while adding the job to the queue')
      }
    }
  }
}

export function useAutoQueue() {
  return {
    async auto(job: FormData) {
      try {
        const response = await api('autoqueue', job)
        if (response) {
          return response
        } else {
          console.error('Response is undefined or null')
          return { success: false, message: 'Response is undefined or null.' }
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while adding the job to the queue')
      }
    }
  }
}

// function to duplicate and rerun job
export function useRerunJob() {
  return {
    async rerunJob(job: Job | undefined, printer: Device) {
      try {
        let printerpk = printer.id
        let jobpk = job?.id

        const response = await api('rerunjob', { jobpk, printerpk }) // pass rerun job the Job object and desired printer
        // const response = {"success": true, "message": "Job rerun successfully"}
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to rerun job. Unexpected response')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to rerun job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while rerunning the job')
      }
    }
  }
}

export function useRemoveJob() {
  return {
    async removeJob(job: Job | undefined) {
      let jobpk = job?.id
      try {
        const response = await api('canceljob', { jobpk })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to remove job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to remove job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while removing the job')
      }
    }
  }
}

export function bumpJobs() {
  return {
    async bumpjob(job: Job, printer: Device, choice: number) {
      try {
        let printerid = printer.id
        let jobid = job.id
        const response = await api('bumpjob', { printerid, jobid, choice })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to bump job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to bump job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while bumping the job')
      }
    }
  }
}

export function useReleaseJob() {
  return {
    async releaseJob(job: Job | undefined, key: number, printerId: number | undefined) {
      try {
        let jobpk = job?.id
        const response = await api('releasejob', { jobpk, key })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to release job. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to release job. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while releasing the job')
      }
    }
  }
}
export function useGetGcode() {
  return {
    async getgcode(job: Job) {
      try {
        const response = await api('getgcode', job)
        return response
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the gcode')
      }
    }
  }
}

export function useGetJobFile() {
  return {
    async getFile(jobid: number) {
      try {
        const response = await api(`getfile?jobid=${jobid}`)
        const file = new Blob([response.file], { type: 'text/plain' })
        const file_name = response.file_name
        saveAs(file, file_name)
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the file')
      }
    }
  }
}

export function useClearSpace(){
  return {
    async clearSpace(){
      try {
        const response = await api('clearspace')
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to clear space. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to clear space. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

// function to constantly update progress of job
export function setupProgressSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('progress_update', (data: any) => {
    const job = printers
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
  })
}

export function setupReleaseSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('release_job', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)
    if (job) {
      console.log(data.released)
      job.released = data.released
    }
  })
}



export function setupJobStatusSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('job_status_update', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      job.status = data.status

      // If the job is complete, cancelled, or errored, stop the timer
      if (['complete', 'cancelled', 'error'].includes(data.status)) {
        if (job.timer) {
          clearInterval(job.timer)
          delete job.timer
        }
      }
    }
  })
}

export function setupPauseFeedbackSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('file_pause_update', (data: any) => {
    const job = printers
    .flatMap((printer: { queue: any }) => printer.queue)
    .find((job: { id: any }) => job?.id === data.job_id)

  if (job) {
    job.file_pause = data.file_pause
    }
  })
}

export function setupTimeSocket(printers: any) {
  // Listen for the 'job_time' event
  socket.on('job_time', (data: any) => {
    // Get the start time and total time from the server
    const job_id = data.job_id
    const total_time = data.total_time

    // Find the job with the matching id
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (!job) {
      console.error(`Job with id ${job_id} not found`)
      return
    }

    // Clear any existing timer
    if (job.timer) {
      clearInterval(job.timer)
      delete job.timer
    }

    // Set the total time for the job
    job.total_time = total_time

    // Set the start time to the current timestamp
    job.start_time = Math.floor(Date.now() / 1000)

    // Create a timer that updates the time every second
    job.timer = startTimer(job, job.start_time, 0, false) // Added fourth argument
  })

  // Listen for the 'job_pause' event
  socket.on('job_pause', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      // Calculate the elapsed time
      const pauseTime = Math.floor(Date.now() / 1000)
      job.elapsed_time = pauseTime - job.start_time

      // Update job.start_time to the pause time
      job.start_time = pauseTime

      // Pause the timer but keep incrementing the elapsed_time and total_time
      if (job.timer) {
        clearInterval(job.timer)
        job.timer = startTimer(job, job.start_time, job.elapsed_time, true)
      }
    }
  })

  // Listen for the 'job_resume' event
  socket.on('job_resume', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (job) {
      // Clear any existing timer
      if (job.timer) {
        clearInterval(job.timer)
        delete job.timer
      }

      // Update job.start_time to the current timestamp
      job.start_time = Math.floor(Date.now() / 1000)

      // Start the timer
      job.timer = startTimer(job, job.start_time, job.elapsed_time, false)
    }
  })
}

function startTimer(job: any, start_time: number, elapsed_time: number, isPaused: boolean) {
  // Ensure start_time and elapsed_time are defined and are numbers
  start_time = start_time || 0
  elapsed_time = elapsed_time || 0

  return setInterval(() => {
    // Calculate the elapsed time
    let current_elapsed_time = Math.floor(Date.now() / 1000) - start_time + elapsed_time

    // Calculate the remaining time
    const remaining_time = isPaused ? job.remaining_time : job.total_time - current_elapsed_time

    // Update the job's time variables
    job.total_time = isPaused ? job.total_time + 1 : job.total_time
    job.elapsed_time = current_elapsed_time
    job.remaining_time = remaining_time

    // If the job is finished, stop the timer
    if (current_elapsed_time >= job.total_time) {
      clearInterval(job.timer)
      delete job.timer
    }
  }, 1000)
}

// function to delete job from db
export function useDeleteJob() {
  return {
    async deleteJob(job: Job) {
      let jobid = job?.id;
      try {
        const response = await api(`deletejob`, { jobid })
        return response;
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while deleting the job')
      }
    }
  }
}

export function useStartJob(){
  return {
    async start(jobid: number, printerid: number){
      try {
        const response = await api(`startprint`, { jobid, printerid })
        return response;
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while starting the job')
      }
    }
  }
}