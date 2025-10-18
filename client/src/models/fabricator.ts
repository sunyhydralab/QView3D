import { type Ref, ref, watchEffect } from 'vue'
import { type Job } from '@/models/job'
import { api } from '@/models/api'
import { onSocketEvent } from '@/services/socket'
import { addToast } from '@/components/Toast.vue'
import { setupSockets } from '@/composables/useWebSockets'

export interface Fabricator {
  device: Record<string, any>
  description: string
  hwid: string
  name?: string
  status?: string
  date?: Date
  id?: number
  error?: string
  canPause?: boolean
  queue?: Job[] //  Store job array to store queue for each printer.
  isQueueExpanded?: boolean
  isInfoExpanded?: boolean
  extruder_temp?: number
  bed_temp?: number
  colorChangeBuffer?: number
  colorbuff?: number
  isSelected: boolean
  consoles?: string[][] 
}

export enum FabricatorStatus {
  TurnOnline = 'ready',
  TurnOffline = 'offline',
  StopPrint = 'complete',
  Error = 'error',
  CancelledPrint = 'cancelled',
  PausePrint = 'paused',
  Printing = 'printing'
}

// list of all registered Fabricators
export const fabricatorList: Ref<Fabricator[]> = ref([])

// update any time the fabricatorList changes
watchEffect(() => {
  console.log('fabricatorList updated:', fabricatorList.value)
})

// Setup socket listeners for real-time fabricator updates
export function setupFabricatorSocketListeners() {
  // Listen for fabricator status updates
  const removeStatusListener = onSocketEvent<Fabricator>('fabricator_status_update', (data) => {
    // Find the fabricator in the list and update its status
    const index = fabricatorList.value.findIndex((f) => f.id === data.id)
    if (index !== -1) {
      // Update only the changed properties
      const updatedFabricator = { ...fabricatorList.value[index], ...data }
      fabricatorList.value[index] = updatedFabricator

      // Notify user about important status changes
      if (data.status && data.status !== fabricatorList.value[index].status) {
        addToast(
          `${updatedFabricator.name || updatedFabricator.description}: Status changed to ${data.status}`,
          data.status === 'Error' ? 'error' : 'info',
        )
      }
    }
  })

  // Listen for new fabricator registrations
  const removeRegistrationListener = onSocketEvent<Fabricator>('fabricator_registered', (data) => {
    // Only add if it's not already in the list
    if (!fabricatorList.value.some((f) => f.id === data.id)) {
      fabricatorList.value.push(data)
      addToast(`New fabricator registered: ${data.name || data.description}`, 'success')
    }
  })

  // Listen for fabricator disconnections
  const removeDisconnectListener = onSocketEvent<{ id: number }>(
    'fabricator_disconnected',
    (data) => {
      const index = fabricatorList.value.findIndex((f) => f.id === data.id)
      if (index !== -1) {
        const fabricator = fabricatorList.value[index]
        fabricatorList.value.splice(index, 1)
        addToast(`Fabricator disconnected: ${fabricator.name || fabricator.description}`, 'warning')
      }
    },
  )

  // Return cleanup function
  return () => {
    removeStatusListener()
    removeRegistrationListener()
    removeDisconnectListener()
  }
}

export async function getConnectedFabricators() {
  return await api('getports')
}

export async function retrieveRegisteredFabricators() {
  const printerInfo = await api('getprinterinfo')
  // Check if the api returned a valid response, if not, return an empty array, to avoid issue where the settings panel never loads.
  fabricatorList.value = printerInfo ? printerInfo : []
  setupSockets(fabricatorList.value)
  // Setup socket listeners after we have the initial data
  setupFabricatorSocketListeners()
  return fabricatorList.value
}

export async function registerFabricator(fabricator: Fabricator) {
  try {
    // set fabricator to printer because the api expects they key, 'printer'
    const printer = fabricator
    fabricator.isSelected = false
    const result = await api('register', { printer })
    addToast(
      `Fabricator ${fabricator.name || fabricator.description} registered successfully`,
      'success',
    )
    return result
  } catch (error) {
    addToast(
      `Failed to register fabricator: ${error instanceof Error ? error.message : 'Unknown error'}`,
      'error',
    )
    throw error
  }
}

export async function deleteFabricator(fabricatorId: number) {
  try {
    console.log(`Attempting to delete printer with ID: ${fabricatorId}`);
    await api('deletefabricator', { fabricator_id: fabricatorId });
    addToast(`Successfully deleted fabricator with the id, ${fabricatorId}`, 'success');
  } catch (error) {
    console.error('Failed to delete printer:', error);
    addToast('Failed to delete printer', 'error');
  }
}

export async function updateFabricatorStatus(fabricatorID: number, newFabricatorStatus: FabricatorStatus) {
  return await api('setstatus', { id: fabricatorID, status: newFabricatorStatus })
}

export async function startPrintAPI(jobID: number, printerID: number) {
  return await api("startprint", { printerid: printerID, jobid: jobID })
}

export async function releaseJob(job: Job, printerID: number, keyY?: number) {
  return await api("releasejob", { jobpk: job.id, key: keyY, printerid: printerID})
}