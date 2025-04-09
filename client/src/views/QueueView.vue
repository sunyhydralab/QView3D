<script setup lang="ts">
import { onUnmounted, ref, computed, watchEffect, onMounted, watch } from 'vue'
import { printers, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, type Job, useMoveJob, useGetFile, useGetJobFile} from '../model/jobs'
import draggable from 'vuedraggable'
import { toast } from '@/model/toast'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCodeThumbnail from '@/components/GCodeThumbnail.vue';
import NoPrinterRobot from '@/components/NoPrinterRobot.vue'
const isLoading = ref(false)
const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()
const { moveJob } = useMoveJob()
const { getFile } = useGetFile()
const { getFileDownload } = useGetJobFile()

const selectedJobs = ref<Array<Job>>([])

let currentJob = ref<Job | null>(null)
let isGcodeImageVisible = ref(false)
const isImageVisible = ref(true)

const primaryColor = ref(window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() || '#7561A9');
const primaryColorActive = ref(window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary-active').trim() || '#51457C');
const secondaryColorActive = ref(window.getComputedStyle(document.documentElement).getPropertyValue('--color-secondary-active').trim() || '#3e7776');
let observer: MutationObserver;

onMounted(() => {
  isLoading.value = true
  observer = new MutationObserver(() => {
    primaryColor.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary').trim() || '#7561A9';
    primaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary-active').trim() || '#51457C';
    secondaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-secondary-active').trim() || '#3e7776';
  });

  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['style'] });

  const modal = document.getElementById('gcodeImageModal')

  modal?.addEventListener('hidden.bs.modal', () => {
    isGcodeImageVisible.value = false
    isImageVisible.value = true
  });
  isLoading.value = false

  // Event listeners for the accordion collapse
  const accordionItems = document.querySelectorAll('.accordion-collapse');
  accordionItems.forEach(item => {
    item.addEventListener('show.bs.collapse', () => {
      const printerId = item.getAttribute('data-printer-id');
      const printer = printers.value.find(p => p.id === Number(printerId));

      if (printer) {
        printer.isQueueExpanded = true;
      }
    });

    item.addEventListener('hide.bs.collapse', () => {
      const printerId = item.getAttribute('data-printer-id');
      const printer = printers.value.find(p => p.id === Number(printerId));

      if (printer) {
        printer.isQueueExpanded = false;
      }
    });
  });
});


onUnmounted(() => {
  for (const printer of printers.value) {
    printer.isQueueExpanded = false
  }
  observer.disconnect();
})

watchEffect(() => {
  primaryColor.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary') || '#7561A9';
  primaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-primary-active') || '#51457C';
  secondaryColorActive.value = window.getComputedStyle(document.documentElement).getPropertyValue('--color-secondary-active') || '#3e7776';
});

const handleRerun = async (job: Job, printer: Device) => {
  await rerunJob(job, printer)
}

const deleteSelectedJobs = async () => {
  isLoading.value = true
  let response = null
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

  for (const printer of printers.value) {
    printer.queue?.forEach((job) => job.queue_selected = false)
  }

  isLoading.value = false
}

const selectAllJobs = (printer: Device) => computed({
  get: () => {
    if (printer.queue?.length === 0) {
      return false;
    }
    return printer.queue?.every((job: Job) => job.queue_selected);
  },
  set: (value) => {
    printer.queue?.forEach((job: Job) => job.queue_selected = value);
  }
});

watch(printers, (printers) => {
  selectedJobs.value = printers.flatMap((printer) => printer.queue?.filter((job) => job.queue_selected) || [])
}, { deep: true })

function capitalizeFirstLetter(string: string | undefined) {
  return string ? string.charAt(0).toUpperCase() + string.slice(1) : ''
}

function statusColor(status: string | undefined) {
  switch (status) {
    case 'ready':
      return secondaryColorActive.value;
    case 'error':
      return '#ad6060';
    case 'offline':
      return getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-font');
    case 'printing':
      return primaryColorActive.value;
    case 'complete':
      return primaryColor.value;
    default:
      return getComputedStyle(document.documentElement, null).getPropertyValue('--color-background-font');
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
    <div :class="['modal-dialog', isImageVisible ? '' : 'modal-xl', 'modal-dialog-centered']">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeImageModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
            <div class="form-check form-switch">
              <label class="form-check-label" for="switchView">{{ isImageVisible ? 'Image' : 'Viewer'
                }}</label>
              <input class="form-check-input" type="checkbox" id="switchView" v-model="isImageVisible">
            </div>
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DImageViewer v-if="isGcodeImageVisible && !isImageVisible" :job="currentJob!" />
            <GCodeThumbnail v-else-if="isGcodeImageVisible && isImageVisible" :job="currentJob!" />
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

    <NoPrinterRobot/>

    <div v-if="printers.length > 0" class="accordion" id="accordionPanelsStayOpenExample">
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
                <span class="status-text" :style="{ color: statusColor(printer.status) }">
                  {{ capitalizeFirstLetter(printer.status) }}
                </span>
              </span>
              <span v-if="printer.queue?.length != 1" style="position: absolute; right: 50px;">{{ printer.queue?.length
      || 0 }} jobs in queue</span>
              <span v-if="printer.queue?.length == 1" style="position: absolute; right: 50px;">{{ printer.queue?.length
      || 0 }} job in queue</span>
            </b>
          </button>
        </h2>
        <div :id="'panelsStayOpen-collapse' + index" class="accordion-collapse collapse"
          :class="{ show: printer.isQueueExpanded }" :aria-labelledby="'panelsStayOpen-heading' + index">
          <div class="accordion-body">
            <div :class="{ 'scrollable': printer.queue!.length > 3 }">
              <table class="table-striped">
                <thead>
                  <tr style="position: sticky; top: 0; z-index: 100;">
                    <th style="width: 102px;">Ticket ID</th>
                    <th style="width: 143px;">Rerun Job</th>
                    <th style="width: 76px;">Position</th>
                    <th style="width: 215px;">Job Title</th>
                    <th style="width: 215px;">File</th>
                    <th style="width: 220px;">Date Added</th>
                    <th style="width: 96px;">Job Status</th>
                    <th style="width: 75px;">Actions</th>
                    <th style="width: 48px;">
                      <div class="checkbox-container">
                        <input class="form-check-input" type="checkbox" :disabled="printer.queue!.length === 0"
                          v-model="selectAllJobs(printer).value" />
                      </div>

                    </th>
                    <th style="width: 58px">Move</th>
                  </tr>
                </thead>
                <draggable v-model="printer.queue" tag="tbody" :animation="300" itemKey="job.id" handle=".handle"
                  dragClass="hidden-ghost" :onEnd="handleDragEnd" v-if="printer.queue && printer.queue.length"
                  :move="isInqueue">
                  <template #item="{ element: job }">
                    <tr :id="job.id.toString()" :data-printer-id="printer.id" :data-job-id="job.id"
                      :data-job-status="job.status" :key="job.id" :class="{ 'printing': job.status === 'printing' }">
                      <td class="truncate" :title="job.td_id">{{ job.td_id }}</td>
                      <td class="text-center">
                        <div class="btn-group w-100">
                          <div class="btn btn-primary" @click="handleRerun(job, printer)">
                            Rerun Job
                          </div>
                          <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                            aria-expanded="false"></div>
                          <div class="dropdown-menu">
                            <div class="dropdown-item" v-for="printer in printers" :key="printer.id"
                              @click="handleRerun(job, printer)">
                              {{ printer.name }}
                            </div>
                          </div>
                        </div>
                      </td>

                      <td class="text-center">
                        <b>
                          {{ printer.queue ? printer.queue.findIndex((j) => j === job) + 1 : '' }}
                        </b>
                      </td>
                      <td class="truncate" :title="job.name">
                        <b>{{ job.name }}</b>
                      </td>
                      <td class="truncate" :title="job.file_name_original">{{ job.file_name_original }}</td>
                      <td class="truncate" :title="job.date">{{ job.date }}</td>
                      <td class="truncate" :title="job.status"
                        v-if="printer.status == 'ready' && printer.queue?.[0].released == 0 && job.status == 'ready'">
                        pending release</td>
                      <td v-else>{{ job.status }}</td>

                      <td style="">
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

                      <td class="text-center">
                        <input class="form-check-input" type="checkbox" v-model="job.queue_selected" :value="job"
                          :disabled="job.status !== 'inqueue'" />
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
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.scrollable {
  max-height: 230px;
  overflow-y: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

td,
th {
  border-top: 0 solid var(--color-border-invert)!important;
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
  border-bottom: 0 !important;
  border-left: 0 !important;
  border-right: 0 !important;
  border-top: 0 !important;
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

.accordion-button {
  box-shadow: none;
}

.accordion-button {
  color: var(--color-text);
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
