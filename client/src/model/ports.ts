import { ref } from 'vue'
import * as myFetch from './myFetch'
import { toast } from './toast'
import { type Job } from './jobs'

export function api(action: string, body?: unknown, method?: string, headers?: any) {
  headers = headers ?? {}
  return myFetch.api(`${action}`, body, method, headers).catch((err) => console.error(err))
}

export interface Device {
  device: Record<string, any>
  description: string
  hwid: string
  name?: string
  status?: string
  date?: Date
  id?: number
  error?: string
  canPause?: number
  queue?: Job[] //  Store job array to store queue for each printer.
  isQueueExpanded?: boolean
  isInfoExpanded?: boolean
  extruder_temp?: number
  bed_temp?: number
  colorChangeBuffer?: number
  colorbuff?: number,
  consoles?: [string[], string[], string[], string[], string[]] // array of debug, info, warning, error and critical console messages
  gcodeLines?: string[] // array of gocde lines sent to the printer
}

export const printers = ref<Device[]>([])

export function useGetPorts() {
  return {
    async ports() {
      try {
        return await api('getports')
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useRegisterPrinter() {
  return {
    async register(printer: Device) {
      try {
        const response = await api('register', { printer })
        if (response) {
          if (response.success === false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to register printer. Unexpected response')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to register printer. Unexpected response')
        }
      } catch (error) {
        console.error(error)
        toast.error('An error occurred while registering the printer')
      }
    }
  }
}

export function useRetrievePrinters() {
  return {
    async retrieve() {
      try {
        return await api('getprinterinfo')
      } catch (error) {
        console.error(error)
      }
    }
  }
}

// gets the printers that have threads information from the server
export function useRetrievePrintersInfo() {
  return {
    async retrieveInfo() {
      try {
        return await api('getprinterinfo')
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useSetStatus() {
  return {
    async setStatus(printerid: number | undefined, status: string) {
      try {
        return await api('setstatus', { printerid, status })
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useHardReset() {
  return {
    async hardReset(printerid: number | undefined) {
      try {
        const response = await api('hardreset', { printerid })
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
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useNullifyJobs() {
  return {
    async nullifyJobs(printerid: number | undefined) {
      try {
        const response = await api('nullifyjobs', { printerid })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to nullify jobs. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to nullify jobs. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useDeletePrinter() {
  return {
    async deletePrinter(fabricator_id: number | undefined) {
      try {
        return await api('deletefabricator', { fabricator_id })
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useRemoveThread() {
  return {
    async removeThread(printerid: number | undefined) {
      try {
        const response = await api('removethread', { printerid })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to remove thread. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to remove thread. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useEditName() {
  return {
    async editName(fabricator_id: number | undefined, name: string) {
      try {
        const response = await api('editname', { fabricator_id, name })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to edit name. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to edit name. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useEditThread() {
  return {
    async editThread(fabricator_id: number | undefined, newname: string) {
      try {
        return await api('editNameInThread', { fabricator_id, newname })
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useDiagnosePrinter() {
  return {
    async diagnose(device: string) {
      try {
        const response = await api('diagnose', { device })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to diagnose printer. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to diagnose printer. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useRepair() {
  return {
    async repair() {
      try {
        const response = await api('repairports')
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to repair ports. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to repair ports. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useMoveHead() {
  return {
    async move(port: string) {
      try {
        const response = await api('movehead', { port })
        if (response) {
          if (response.success == false) {
            toast.error(response.message)
          } else if (response.success === true) {
            toast.success(response.message)
          } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to move head. Unexpected response.')
          }
        } else {
          console.error('Response is undefined or null')
          toast.error('Failed to move head. Unexpected response')
        }
        return response
      } catch (error) {
        console.error(error)
      }
    }
  }
}

export function useMovePrinterList() {
  return {
    async movePrinterList(printers: Device[]) {
      try {
        // make new array of printer id's in the order they are in the printers array
        const printersIds = printers.map((printer) => printer.id)
        return await api('moveprinterlist', { printersIds })
      } catch (error) {
        console.error(error)
      }
    }
  }
}
