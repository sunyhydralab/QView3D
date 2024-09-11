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
            return await doHandleApi('getports', undefined, undefined, undefined, true)
        }
    }
}

export function useRegisterPrinter() {
    return {
        async register(printer: Device) {
            await doHandleApi('register', printer, 'register printer', 'registering the printer')
        }
    }
}

export function useRetrievePrinters() {
    return {
        async retrieve() {
            const res = await doHandleApi('getprinters', undefined, undefined, undefined, true)
            return res.printers
        }
    }
}

// gets the printers that have threads information from the server
export function useRetrievePrintersInfo() {
    return {
        async retrieveInfo() {
            return await doHandleApi('getprinterinfo')
        }
    }
}

export function useSetStatus() {
    return {
        async setStatus(printerid: number | undefined, status: string) {
            await doHandleApi('setstatus', { printerid, status })
        }
    }
}

export function useHardReset() {
    return {
        async hardReset(printerid: number | undefined) {
            await doHandleApi('hardreset', { printerid }, 'release job', 'hard resetting the printer')
        }
    }
}

export function useNullifyJobs() {
    return {
        async nullifyJobs(printerid: number | undefined) {
            await doHandleApi('nullifyjobs', { printerid }, 'nullify jobs', 'nullifying jobs')
        }
    }
}

export function useDeletePrinter() {
    return {
        async deletePrinter(printerid: number | undefined) {
           await doHandleApi('deleteprinter', { printerid }, 'delete printer', 'deleting the printer')
        }
    }
}

export function useRemoveThread() {
    return {
        async removeThread(printerid: number | undefined) {
            await doHandleApi('removethread', { printerid }, 'remove thread', 'removing the thread')
        }
    }
}

export function useEditName() {
    return {
        async editName(printerid: number | undefined, name: string) {
            await doHandleApi('editname', { printerid, name }, 'edit name', 'editing the name')
            
        }
    }
}

export function useEditThread() {
    return {
        async editThread(printerid: number | undefined, newname: string) {
            return await doHandleApi('editthread', { printerid, newname }, undefined, undefined, true);
        }
    }
}

export function useDiagnosePrinter() {
    return {
        async diagnose(device: string) {
            return await doHandleApi('diagnose', { device }, 'diagnose printer', 'diagnosing the printer', true)
        }
    }
}

export function useRepair() {
    return {
        async repair() {
            await doHandleApi('repairports', undefined, 'repair ports', 'repairing the ports')
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