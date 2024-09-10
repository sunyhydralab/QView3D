import { useRouter } from 'vue-router'
import { ref, computed, onUnmounted } from 'vue'
import * as myFetch from './myFetch'
import { toast } from './toast'
import { type Job } from './jobs'
import { socket } from './myFetch'

export function api(action: string, body?: unknown, method?: string, headers?: any) {
    headers = headers ?? {}
    return myFetch.api(`${action}`, body, method, headers).catch((err) => console.log(err))
}
/**
@description This function is used to handle the api calls on the client side.
@param action The API action to be performed.
@param body The body of the request.
@param failureText The text to be shown in the toast message if the response success is false. if null, no toast will be shown.
@param errorText The text to be shown in the toast message if there is no response at all.
@param returnResponse If true, the response will be returned.
@param noSuccessToast If true, the success and error toasts will not be shown, but an error toast will be shown if the response is null or undefined.
@return The response of the API call, but only if returnResponse is true.
 **/
export async function doHandleApi(action: string, body?: unknown, failureText?: string, errorText?: string, returnResponse?: boolean, noSuccessToast?: boolean) {
    try {
        const response = await api(action, body)
        if (failureText) {
            if (response) {
                if(!noSuccessToast) {
                    if (response.success === false) {
                        toast.error(response.message)
                    } else if (response.success === true) {
                        toast.success(response.message)
                    } else {
                        console.error('Unexpected response:', response)
                        toast.error('Failed to ' + failureText + '. Unexpected response')
                    }
                }
            } else {
                console.error('Response is undefined or null')
                toast.error('Failed to ' + failureText + '. Unexpected response')
            }
        }
        if (returnResponse) return response
    } catch (error) {
        console.error(error)
        if (errorText) toast.error('An error occurred while ' + errorText)
    }
}

export interface Device {
    device: string
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
}

export const printers = ref<Device[]>([])

export function useGetPorts() {
    return {
        async ports() {
            return doHandleApi('getports', undefined, undefined, undefined, true)
        }
    }
}

export function useRegisterPrinter() {
    return {
        async register(printer: Device) {
            doHandleApi('register', printer, 'register printer', 'registering the printer')
        }
    }
}

export function useRetrievePrinters() {
    return {
        async retrieve() {
            return doHandleApi('getprinters', undefined, undefined, undefined, true).printers
        }
    }
}

// gets the printers that have threads information from the server
export function useRetrievePrintersInfo() {
    return {
        async retrieveInfo() {
            doHandleApi('getprinterinfo')
        }
    }
}

export function useSetStatus() {
    return {
        async setStatus(printerid: number | undefined, status: string) {
            doHandleApi('setstatus', { printerid, status })
        }
    }
}

export function useHardReset() {
    return {
        async hardReset(printerid: number | undefined) {
            doHandleApi('hardreset', { printerid }, 'release job', 'hard resetting the printer')
        }
    }
}

export function useNullifyJobs() {
    return {
        async nullifyJobs(printerid: number | undefined) {
            doHandleApi('nullifyjobs', { printerid }, 'nullify jobs', 'nullifying jobs')
        }
    }
}

export function useDeletePrinter() {
    return {
        async deletePrinter(printerid: number | undefined) {
            doHandleApi('deleteprinter', { printerid }, 'delete printer', 'deleting the printer')
        }
    }
}

export function useRemoveThread() {
    return {
        async removeThread(printerid: number | undefined) {
            doHandleApi('removethread', { printerid }, 'remove thread', 'removing the thread')
        }
    }
}

export function useEditName() {
    return {
        async editName(printerid: number | undefined, name: string) {
            doHandleApi('editname', { printerid, name }, 'edit name', 'editing the name')
            
        }
    }
}

export function useEditThread() {
    return {
        async editThread(printerid: number | undefined, newname: string) {
            return doHandleApi('editthread', { printerid, newname }, undefined, undefined, true);
        }
    }
}

export function useDiagnosePrinter() {
    return {
        async diagnose(device: string) {
            doHandleApi('diagnose', { device }, 'diagnose printer', 'diagnosing the printer')
        }
    }
}

export function useRepair() {
    return {
        async repair() {
            doHandleApi('repairports', undefined, 'repair ports', 'repairing the ports')
        }
    }
}

export function useMoveHead() {
    return {
        async move(port: string) {
            doHandleApi('movehead', { port }, 'move head', 'moving the head')
        }
    }
}

export function useMovePrinterList() {
    return {
        async movePrinterList(printers: Device[]) {
            return doHandleApi('moveprinterlist', { printers }, undefined, undefined, true)
        }
    }
}