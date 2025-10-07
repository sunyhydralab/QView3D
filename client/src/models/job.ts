import { ref, watchEffect } from 'vue'
import { api } from '@/models/api'
import { onSocketEvent } from '@/services/socket'
import { addToast } from '@/components/Toast.vue'

export interface Job {
    id: number
    name: string
    file: File
    download_link?: string
    file_name_original: string
    date?: Date
    status?: string
    progress?: number //store progress of job
    gcode_num?: number //store gcode of job
    printer: string //store printer name
    printerid: number
  
    td_id: number //store td_id of job
  
    max_layer_height?: number //store max layer height of job
    current_layer_height?: number //store current layer height of job
  
    errorid?: number
    error?: string // store issue name
  
    comments?: string // store comments
  
    extruded?: number
    filament?: string
  
    file_pause: boolean
    priority?: string
    favorite?: boolean
    released?: boolean
    job_server?: [number, Date | string, Date | string, Date | string] // this saves all the data from the backend.Only changed if there is a pause involved.
  
    job_client?: {
      // this is frontend data CALCULATED based on the backend data
      total_time: number
      eta: number
      elapsed_time: number
      extra_time: number
      remaining_time: number
    }
    time_started?: number
    colorbuff?: number 
    printer_name?: string
    queue_selected?: boolean
}

// Store for jobs history
export const jobHistory = ref<Job[]>([])

// update any time the jobHistory changes
watchEffect(() => {
  console.log('job history updated:', jobHistory.value)
})

// Setup socket listeners for real-time job updates
export function setupJobSocketListeners() {
  // Listen for job status/progress updates
  const removeJobUpdateListener = onSocketEvent<Partial<Job>>('job_update', (data) => {
    if (!data.id) return

    // Find if the job exists in our history
    const index = jobHistory.value.findIndex(job => job.id === data.id)
    
    if (index !== -1) {
      // Update existing job with new data
      const previousStatus = jobHistory.value[index].status
      jobHistory.value[index] = { ...jobHistory.value[index], ...data }
      
      // Notify on important status changes
      if (data.status && data.status !== previousStatus) {
        const jobName = jobHistory.value[index].name
        let toastType: 'success' | 'error' | 'info' | 'warning' = 'info'
        
        if (data.status === 'Done') toastType = 'success'
        else if (data.status === 'Error') toastType = 'error'
        else if (data.status === 'Paused') toastType = 'warning'
        
        addToast(`Job '${jobName}' status changed to ${data.status}`, toastType)
      }
    } else if (data.id && data.name) {
      // It's a new job we don't have yet, add it to our history
      jobHistory.value.push(data as Job)
    }
  })
  
  // Listen for job completed events
  const removeJobCompletedListener = onSocketEvent<{job: Job}>('job_completed', (data) => {
    const index = jobHistory.value.findIndex(job => job.id === data.job.id)
    
    if (index !== -1) {
      // Update the job in our history
      jobHistory.value[index] = { ...jobHistory.value[index], ...data.job, status: 'Done' }
    } else {
      // Add the completed job to our history
      jobHistory.value.push({ ...data.job, status: 'Done' })
    }
    
    addToast(`Job '${data.job.name}' completed successfully!`, 'success')
  })
  
  // Listen for job error events
  const removeJobErrorListener = onSocketEvent<{job: Job, error: string}>('job_error', (data) => {
    const index = jobHistory.value.findIndex(job => job.id === data.job.id)
    
    if (index !== -1) {
      // Update the job in our history
      jobHistory.value[index] = { 
        ...jobHistory.value[index], 
        ...data.job, 
        status: 'Error',
        error: data.error
      }
    } else {
      // Add the errored job to our history
      jobHistory.value.push({ 
        ...data.job, 
        status: 'Error',
        error: data.error 
      })
    }
    
    addToast(`Error in job '${data.job.name}': ${data.error}`, 'error')
  })
  
  // Return cleanup function
  return () => {
    removeJobUpdateListener()
    removeJobCompletedListener()
    removeJobErrorListener()
  }
}

/*
export async function getAllJobs() {
  try {
    jobHistory.value = await api('getjobs')
    // Setup socket listeners after initial data load
    setupJobSocketListeners()
    return jobHistory.value
  } catch (error) {
    addToast(`Failed to fetch jobs: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
    throw error
  }
}
  */
 export async function getAllJobs() {
  try {
    jobHistory.value = await api('getjobs')
    // Setup socket listeners after initial data load
    setupJobSocketListeners()
    return jobHistory.value
  } catch (error) {
    addToast(`Failed to fetch jobs: ${error instanceof Error ? error.message : 'Using mock jobs'}`, 'warning')
// Properly typed mock jobs
    const mockJobs: Job[] = [
      {
        id: 101,
        name: 'Mock Job 1',
        file: new File([''], 'mock1.gcode', { type: 'text/plain' }),
        file_name_original: 'mock1.gcode',
        file_pause: false,
        printer: 'Emulator Printer (Mock) 1',
        printerid: 101, // match emulator printer id
        td_id: 1,
      },
      {
        id: 102,
        name: 'Mock Job 2',
        file: new File([''], 'mock2.gcode', { type: 'text/plain' }),
        file_name_original: 'mock2.gcode',
        file_pause: false,
        printer: 'Emulator Printer (Mock) 2',
        printerid: 102,
        td_id: 2,
      },
    ]

    jobHistory.value = mockJobs
    return jobHistory.value
  }
}

export async function addJobToQueue(job : FormData) {
  return api('addjobtoqueue', job)
}

export async function autoQueue(job: FormData) {
  try {
    const result = await api('autoqueue', job)
    const jobName = job.get('name') as string
    addToast(`Job '${jobName}' successfully added to queue`, 'success')
    return result
  } catch (error) {
    addToast(`Failed to queue job: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
    throw error
  }
}

export async function removeJob(jobarr: number[]) {
  try {
    const response = await api('cancelfromqueue', { jobarr })
    if (response) {
      return response
    } else {
      console.error('Response is undefined or null')
    }
  } catch (error) {
    console.error(error)
  }
}
