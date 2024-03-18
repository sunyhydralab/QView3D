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
  favorite?: boolean
  released?: number
  job_server?: [number, Date, Date, Date] // this saves all of the data from the backend.Only changed if there is a pause involved.

  job_client?: {
    // this is frontend data CALCULATED based on the backend data
    total_time: number
    eta: number
    elapsed_time: number
    extra_time: number
    remaining_time: number
  }
  timer?: NodeJS.Timeout
}

export function jobTime(job: Job, printers: any) {
  const printerid = job.printerid
  const printer = printers.find((printer: { id: number }) => printer.id === printerid)

  // job.job_client!.remaining_time = NaN

  const updateJobTime = () => {
    if (printer.status !== 'printing') {
      clearInterval(job.timer)
      delete job.timer
      return
    }

    let totalTime = job.job_server![0] 
    job.job_client!.total_time = totalTime * 1000

    let eta = job.job_server![1] instanceof Date ? job.job_server![1].getTime() : job.job_server![1]
    job.job_client!.eta = eta + job.job_client!.extra_time

    if (printer.status === 'printing' || printer.status === 'colorchange' || printer.status === 'paused') {
      const now = Date.now();
      const elapsedTime = now - new Date(job.job_server![2]).getTime();
      job.job_client!.elapsed_time = Math.round(elapsedTime / 1000) * 1000;
      if(!isNaN(job.job_client!.elapsed_time)){
        if(job.job_client!.elapsed_time <= job.job_client!.total_time){
          job.job_client!.remaining_time = job.job_client!.total_time - job.job_client!.elapsed_time
        }
      }
    }

    if (job.job_client!.elapsed_time > job.job_client!.total_time) {
      job.job_client!.extra_time = Date.now() - eta
    }

    // Update elapsed_time after the first second
    if (job.job_client!.elapsed_time === 0) {
      job.job_client!.elapsed_time = 1;
    }
  }

  // Call updateJobTime immediately when jobTime is called
  updateJobTime();

  // Continue to call updateJobTime at regular intervals
  job.timer = setInterval(updateJobTime, 1000)
}

export function setupTimeSocket(printers: any) {
  // Always set up the socket connection and event listener
  socket.on('set_time', (data: any) => {
    const job = printers
      .flatMap((printer: { queue: any }) => printer.queue)
      .find((job: { id: any }) => job?.id === data.job_id)

    if (!job.job_client || !job.job_server) {
      job.job_client = {
        total_time: 0,
        eta: 0,
        elapsed_time: 0,
        extra_time: 0,
        remaining_time: NaN
      }
      // job.job_server = ['00:00:00', '00:00:00', '00:00:00', '00:00:00']
      job.job_server = [0, '00:00:00', '00:00:00', '00:00:00']

    }

    if(typeof(data.new_time) === 'number'){
      job.job_server[data.index] = data.new_time
    }else{
      job.job_server[data.index] = Date.parse(data.new_time)
    }

    jobTime(job, printers)
  })
}

export function useGetJobs() {
  return {
    async jobhistory(page: number, pageSize: number, printerIds?: number[], oldestFirst?: boolean, searchJob: string = '', searchCriteria: string = '') {
      try {
        const response = await api(
          `getjobs?page=${page}&pageSize=${pageSize}&printerIds=${JSON.stringify(printerIds)}&oldestFirst=${oldestFirst}&searchJob=${encodeURIComponent(searchJob)}&searchCriteria=${encodeURIComponent(searchCriteria)}`
        )
        return response
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the jobs')
      }
    },
    async getFavoriteJobs() {
      try {
        const response = await api('getfavoritejobs')
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
          // if (response.success == false) {
          //   toast.error(response.message)
          // } else if (response.success === true) {
          //   toast.success(response.message)
          // } else {
          //   console.error('Unexpected response:', response)
          //   toast.error('Failed to queue job. Unexpected response')
          // }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to queue job. Unexpected response')
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
          return response
          // if (response.success == false) {
          //   toast.error(response.message)
          // } else if (response.success === true) {
          //   toast.success(response.message)
          // } else {
          //   console.error('Unexpected response:', response)
          //   toast.error('Failed to remove job. Unexpected response.')
          // }
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

export function useGetFile() {
  return {
    async getFile(job: Job) {
      try {
        const jobid = job.id
        const response = await api(`getfile?jobid=${jobid}`)
        const file = new File([response.file], response.file_name, { type: 'text/plain' })
        return file
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while retrieving the file')
      }
    }
  }
}

export function useClearSpace() {
  return {
    async clearSpace() {
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

export function useFavoriteJob() {
  return {
    async favorite(job: Job, favorite: boolean) {
      let jobid = job?.id;
      try {
        const response = await api(`favoritejob`, { jobid, favorite })
        if (response.success) {
          job.favorite = favorite ? true : false;
        }
        return response;
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while favoriting the job')
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
    }
  })
}

// function to delete job from db
export function useDeleteJob() {
  return {
    async deleteJob(job: Job) {
      let jobid = job?.id
      try {
        const response = await api(`deletejob`, { jobid })
        return response
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