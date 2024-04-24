<script setup lang="ts">
import { onUnmounted, ref, computed, watchEffect, onMounted } from 'vue'
import { printers, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, type Job, useMoveJob, useGetFile, useGetJobFile } from '../model/jobs'
import draggable from 'vuedraggable'
import { toast } from '@/model/toast'
import { useRouter } from 'vue-router'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'

const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()
const { moveJob } = useMoveJob()
const { getFile } = useGetFile()
const { getFileDownload } = useGetJobFile()

const selectedJobs = ref<Array<Job>>([])
const selectAllCheckboxMap = ref<Record<string, boolean>>({})

let currentJob = ref<Job | null>(null)
let isGcodeImageVisible = ref(false)
let selectAllCheckbox = ref(false)

const primaryColor = ref('');
const primaryColorActive = ref('');
const successColorActive = ref('');
let observer: MutationObserver;

onMounted(() => {
  observer = new MutationObserver(() => {
    primaryColor.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9';
    primaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color-active').trim() || '#51457C';
    successColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-success-color-active').trim() || '#3e7776';
  });

  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });

  const modal = document.getElementById('gcodeImageModal')

  modal?.addEventListener('hidden.bs.modal', () => {
    isGcodeImageVisible.value = false
  });
});


onUnmounted(() => {
  for (const printer of printers.value) {
    printer.isQueueExpanded = false
  }
  observer.disconnect();
})

watchEffect(() => {
  primaryColor.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color').trim() || '#7561A9';
  primaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-primary-color-active').trim() || '#51457C';
  successColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--bs-success-color-active').trim() || '#3e7776';
});

const handleRerun = async (job: Job, printer: Device) => {
  await rerunJob(job, printer)
}

const deleteSelectedJobs = async () => {
  let response = null
  // Loop through the selected jobs and remove them from the printer's queue
  const selectedJobIds = computed(() => selectedJobs.value.map(job => job.id));

  response = await removeJob(selectedJobIds.value);
  if (response.success == false) {
    toast.error(response.message)
  } else if (response.success === true) {
    toast.success(response.message)
  } else {
    console.error('Unexpected response:', response)
    toast.error('Failed to remove job. Unexpected response.')
  }
  // Clear the selected jobs array
  selectedJobs.value = []
  selectAllCheckbox.value = false
}

const selectAllJobs = (printer: Device) => {
  if (printer !== undefined && printer.queue !== undefined) {
    // Toggle the "Select All" checkbox state for the current printer
    selectAllCheckboxMap.value[printer.id!] = !selectAllCheckboxMap.value[printer.id!]

    if (selectAllCheckboxMap.value[printer.id!]) {
      // If the "Select All" checkbox for the current printer is checked,
      // add all jobs from the current printer to the selectedJobs array
      // but only if the job's status is 'inqueue'
      selectedJobs.value = [
        ...selectedJobs.value,
        ...printer.queue.filter(job => job.status === 'inqueue')
      ];
    } else {
      // Otherwise, remove all jobs from the current printer from the selectedJobs array
      selectedJobs.value = selectedJobs.value.filter((job) => job.printerid !== printer.id)
    }
  }
}

function capitalizeFirstLetter(string: string | undefined) {
  return string ? string.charAt(0).toUpperCase() + string.slice(1) : ''
}

function statusColor(status: string | undefined) {
  switch (status) {
    case 'ready':
      return successColorActive.value;
    case 'error':
      return '#ad6060';
    case 'offline':
      return 'black';
    case 'printing':
      return primaryColorActive.value;
    case 'complete':
      return primaryColor.value;
    default:
      return 'black';
  }
}

const handleDragEnd = async (evt: any) => {
  const printerId = Number(evt.item.dataset.printerId)
  const arr = Array.from(evt.to.children).map((child: any) => Number(child.dataset.jobId))
  await moveJob(printerId, arr)
}

const isInqueue = (evt: any) => {
  return evt.relatedContext.element.status === 'inqueue'
}

const openModal = async (job: Job, printerName: string, num: number, printer: Device) => {
  currentJob.value = job
  currentJob.value.printer = printerName
  if (num == 1) {
    // isGcodeLiveViewVisible.value = true
  } else if (num == 2) {
    isGcodeImageVisible.value = true
    if (currentJob.value) {
      const file = await getFile(currentJob.value)
      if (file) {
        currentJob.value.file = file
      }
    }
  }
}
</script>

<template>
  <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeImageModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob!" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true"
    data-bs-backdrop="static">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="exampleModalLabel">
            Removing {{ selectedJobs.length }} job(s) from queue!
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>
            Are you sure you want to remove these job(s) from queue? Job will be saved to history
            with a final status of <i>cancelled</i>.
          </p>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button type="button" class="btn btn-danger" data-bs-dismiss="modal" @click="deleteSelectedJobs">
            Remove
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="container">
    <!-- <b>Queue View</b> -->

    <div class="row w-100" style="margin-bottom: 0.5rem">
      <div class="col-2 text-start" style="padding-left: 0">

      </div>
      <div class="col-8"></div>
      <div class="col-2 text-end" style="padding-right: 0">
        <button class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#exampleModal"
          :disabled="selectedJobs.length === 0">
          Remove
        </button>
      </div>
    </div>

    <div v-if="printers.length === 0">
      No printers available. Either register a printer
      <RouterLink class="routerLink" to="/registration"> here </RouterLink>, or restart the server.
    </div>

    <div v-else class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item" v-for="(printer, index) in printers" :key="printer.id">
        <h2 class="accordion-header" :id="'panelsStayOpen-heading' + index">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
            :data-bs-target="'#panelsStayOpen-collapse' + index" :aria-expanded="printer.isQueueExpanded"
            :aria-controls="'panelsStayOpen-collapse' + index" :class="{ collapsed: !printer.isQueueExpanded }">
            <b>{{ printer.name }}:&nbsp;

              <span v-if="printer.status === 'printing' && printer.queue?.[0]?.released === 0">
                Pending Release
              </span>
              <span v-else>
                <span class="status-text" :style="{ color: statusColor(printer.status) }">{{
              capitalizeFirstLetter(printer.status)
            }}
                </span>
              </span>
            </b>
          </button>
        </h2>
        <div :id="'panelsStayOpen-collapse' + index" class="accordion-collapse collapse"
          :class="{ show: printer.isQueueExpanded }" :aria-labelledby="'panelsStayOpen-heading' + index"
          @show.bs.collapse="printer.isQueueExpanded = !printer.isQueueExpanded">
          <div class="accordion-body">
            <div :class="{ 'scrollable': printer.queue!.length > 4 }">
              <table class="table-striped">
                <thead>
                  <tr style="position: sticky; top: 0; z-index: 100; background-color: white;">
                    <th class="col-1">Ticket ID</th>
                    <th class="col-2">Rerun Job</th>
                    <th class="col-1">Position</th>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Date Added</th>
                    <th class="col-1">Job Status</th>
                    <th class="col-checkbox">
                      <div class="checkbox-container">
                        <input class="form-check-input" type="checkbox" @change="() => selectAllJobs(printer)"
                          :disabled="printer.queue!.length === 0" v-model="selectAllCheckbox" />
                      </div>
                    </th>
                    <th>Actions</th>
                    <th style="width: 0">Move</th>
                  </tr>
                </thead>
                <draggable v-model="printer.queue" tag="tbody" :animation="300" itemKey="job.id" handle=".handle"
                  dragClass="hidden-ghost" :onEnd="handleDragEnd" v-if="printer.queue && printer.queue.length"
                  :move="isInqueue">
                  <template #item="{ element: job }">
                    <tr :id="job.id.toString()" :data-printer-id="printer.id" :data-job-id="job.id"
                      :data-job-status="job.status" :key="job.id" :class="{ printing: job.status === 'printing' }">
                      <td>{{ job.id }}</td>

                      <td class="text-center">
                        <div class="btn-group w-100">
                          <div class="btn btn-primary" @click="handleRerun(job, printer)">
                            Rerun Job
                          </div>
                          <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                            aria-expanded="false"></div>
                          <div class="dropdown-menu">
                            <div class="dropdown-item"
                              v-for="otherPrinter in printers.filter((p) => p.id !== printer.id)" :key="otherPrinter.id"
                              @click="handleRerun(job, otherPrinter)">
                              {{ otherPrinter.name }}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td class="text-center">
                        <b>
                          {{ printer.queue ? printer.queue.findIndex((j) => j === job) + 1 : '' }}
                        </b>
                      </td>
                      <td>
                        <b>{{ job.name }}</b>
                      </td>
                      <td>{{ job.file_name_original }}</td>
                      <td>{{ job.date }}</td>
                      <td
                        v-if="printer.queue && printer.status == 'printing' && printer.queue?.[0].released == 0 && job.status == 'printing'">
                        Pending release</td>
                      <td v-else>{{ job.status }}</td>

                      <td class="text-center">
                        <input class="form-check-input" type="checkbox" v-model="selectedJobs" :value="job" />
                      </td>

                      <td style="width:">
                        <div class="dropdown">
                          <div style="
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100%;
                          ">
                            <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                              style="background: none; border: none">
                              <i class="fa-solid fa-bars"></i>
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                              <li>
                                <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                  data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                                  @click="printer.name && openModal(job, printer.name, 2, printer)">
                                  <i class="fa-solid fa-image"></i>
                                  <span class="ms-2">GCode Image</span>
                                </a>
                              </li>
                              <li>
                                <a class="dropdown-item d-flex align-items-center" @click="getFileDownload(job.id)"
                                  :disabled="job.file_name_original.includes('.gcode:')">
                                  <i class="fas fa-download"></i>
                                  <span class="ms-2">Download</span>
                                </a>
                              </li>
                            </ul>
                          </div>
                        </div>
                      </td>

                      <td class="text-center handle" :class="{ 'not-draggable': job.status !== 'inqueue' }">
                        <i class="fas fa-grip-vertical" :class="{ 'icon-disabled': job.status !== 'inqueue' }"></i>
                      </td>
                    </tr>
                  </template>
                </draggable>

                <tr v-if="printer.queue && printer.queue.length === 0">
                  <td colspan="10" class="text-center">No jobs in queue</td>
                </tr>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrollable {
  max-height: 260px;
  overflow-y: auto;
}

table {
  color: #1b1b1b;
  background-color: #d8d8d8;
  width: 100%;
  border-collapse: collapse;
}

td,
th {
  border-top: 0px solid #929292 !important;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding-left: 0.5rem;
}

.dropdown-item i {
  width: 20px;
}

.dropdown-item span {
  margin-left: 10px;
}

.btn-circle {
  width: 30px;
  height: 30px;
  padding: 0.375em 0;
  border-radius: 50%;
  font-size: 0.75em;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.hidden-ghost {
  opacity: 0;
}

.handle {
  cursor: grab;
}

.handle:active {
  cursor: grabbing;
}

.checkbox-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.icon-disabled {
  color: #6e7073;
}

.not-draggable {
  pointer-events: none;
}

table {
  border-bottom: 0px !important;
  border-left: 0px !important;
  border-right: 0px !important;
  border-top: 0px !important;
}

table tr:last-child td {
  border-bottom: none !important;
}

.accordion-body {
  padding: 0;
}

/* HARDCODED */
.accordion-item {
  width: 1296px;
  overflow: hidden !important;
}

.accordion-button:not(.collapsed) {
  background-color: #9f9f9f;
}

.accordion-button {
  box-shadow: none;
}

.accordion-button {
  color: black;
  display: flex;
}

.accordion-button:not(.collapsed)::after {
  background-image: var(--bs-accordion-btn-icon);
}

.printerrerun {
  cursor: pointer;
  padding: 12px 16px;
}

.modal-backdrop {
  display: none;
}
</style>
