// ts file to retrieve job information
import { useRouter } from 'vue-router'
import { api } from './ports'
import { toast } from './toast'

export interface Job {
  name: string
  file: File
  file_name: string 
  date?: Date
  status?: string
  printer: string; //store printer name
  printerid: number
}

export function useGetJobs() {
  return {
    async jobhistory() {
      try {
        const response = await api('getjobs')
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
        console.log('job:', job)
        const response = await api('addjobtoqueue', job)
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to add job to queue. Unexpected response')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to add job to queue. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while adding the job to the queue')
      }
    }
  }
}
