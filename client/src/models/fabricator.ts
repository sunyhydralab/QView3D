import { ref } from 'vue'
import { type Job } from '@/models/job'
import { api } from '@/models/api'

export interface Fabricator {
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
  }


export const FabricatorList = ref<Fabricator[]>([])

export async function getPorts() {
    return api('getports');
}

export async function retrievePrinters() {
      return await api('getprinterinfo')
}