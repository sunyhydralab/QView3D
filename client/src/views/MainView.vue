<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { printers, useSetStatus, useMovePrinterList, type Device } from '@/model/ports';
import draggable from 'vuedraggable';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue';
import GCodeThumbnail from '@/components/GCodeThumbnail.vue';
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import { useAssignIssue, useGetIssues, type Issue } from '@/model/issues';
import { jobTime, useAssignComment, useGetFile, useGetJobFile, useReleaseJob, useStartJob, type Job } from '@/model/jobs';
import { useRouter } from 'vue-router';

const { assign } = useAssignIssue();
const { assignComment } = useAssignComment();
const { releaseJob } = useReleaseJob();
const { issues } = useGetIssues();
const { getFile } = useGetFile();
const { setStatus } = useSetStatus();
const { start } = useStartJob();
const { getFileDownload } = useGetJobFile();
const { movePrinterList } = useMovePrinterList();

const router = useRouter();

// State for selected job and issue comments
const selectedIssue = ref<Issue>();
const selectedJob = ref<Job>();
let jobComments = ref('');

// Current job and printer being worked on
let currentJob = ref<Job>();
let currentPrinter = ref<Device>();

// State for issues and visibility of GCode modals
let issuelist = ref<Array<Issue>>([]);
let isGcodeImageVisible = ref(false);
const isImageVisible = ref(true);
let isGcodeLiveViewVisible = ref(false);

// Expanded printer state
let expandedState: (string | undefined)[] = [];

// Table headers
const headers = [
  { text: 'ID', style: 'width: 64px; position: relative;' },
  { text: 'Printer Name', style: 'width: 130px; position: relative;' },
  { text: 'Printer Status', style: 'width: 142px; position: relative;' },
  { text: 'Job Name', style: 'width: 110px; position: relative;' },
  { text: 'File', style: 'width: 110px; position: relative;' },
  { text: 'Printer Options', style: 'width: 314px; position: relative;' },
  { text: 'Progress', style: 'width: 315px; position: relative;' },
  { text: 'Actions', style: 'width: 75px; position: relative;' },
  { text: 'Move', style: 'width: 58px; position: relative;' }
];

// On component mount, fetch issues and initialize modals
onMounted(async () => {
  issuelist.value = await issues();
  setupModalEvents();
  initResizableColumns();
});

// Format time for display
function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60);
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60);
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24);

  return [hours, minutes, seconds]
      .map(unit => (unit < 10 ? '0' + unit : unit))
      .join(':') || '<i>Waiting...</i>';
}

// Format ETA for display
function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds);
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });
  return !isNaN(date.getTime()) && timeString !== '07:00 PM' ? timeString : '<i>Waiting...</i>';
}

// Collapse and restore expanded printer state
const collapseAll = () => {
  expandedState = printers.value.filter(printer => printer.isInfoExpanded).map(printer => printer.id?.toString());
  printers.value.forEach(printer => printer.isInfoExpanded = false);
};

const restoreExpandedState = () => {
  printers.value.forEach(printer => {
    if (expandedState.includes(printer.id?.toString())) {
      printer.isInfoExpanded = true;
    }
  });
};

// Assign issue and comment to a job
const doAssignIssue = async () => {
  if (!selectedJob.value) return;

  await assignComment(selectedJob.value, jobComments.value);
  await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid);

  if (selectedIssue.value) {
    await assign(selectedIssue.value.id, selectedJob.value.id);
  }

  selectedJob.value.comments = jobComments.value;
  resetSelections();
};

// Open modals for GCode views
const openModal = async (job: Job, printerName: string, viewType: number, printer: Device) => {
  await jobTime(job, printers);
  currentJob.value = job;
  currentJob.value.printer = printerName;
  currentPrinter.value = printer;

  viewType === 1 ? openLiveViewer() : openImageViewer();
};

// Set job for issue assignment
const setJob = (job: Job) => {
  jobComments.value = job.comments || '';
  selectedJob.value = job;
};

// Set printer status and trigger start/stop of print jobs
const setPrinterStatus = async (printer: Device, status: string) => {
  await setStatus(printer.id, status);
  resetSelectElement();
};

const startPrint = async (printerid: number, jobid: number) => {
  await start(jobid, printerid);
};

// Release printer resources
const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {
  const printer = printers.value.find(p => p.id === printerIdToPrintTo);
  if (printer) {
    printer.error = '';
    printer.extruder_temp = 0;
    printer.bed_temp = 0;
  }

  await releaseJob(jobToFind, key, printerIdToPrintTo);
};

// Handle drag end event for rearranging printers
const handleDragEnd = async () => {
  await movePrinterList(printers.value);
};

// Setup event listeners for modals to reset visibility on close
function setupModalEvents() {
  const imageModal = document.getElementById('gcodeImageModal');
  const liveModal = document.getElementById('gcodeLiveViewModal');

  imageModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeImageVisible.value = false;
    isImageVisible.value = true;
  });

  liveModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeLiveViewVisible.value = false;
  });
}

// Initialize resizable columns by adding event listeners for drag resizing
function initResizableColumns() {
  const table = document.querySelector("table");
  const cols = table.querySelectorAll("th");
  let isResizing = false, startX, startWidth;

  cols.forEach(col => {
    const resizer = col.querySelector(".resize-handle");

    resizer.addEventListener("mousedown", e => {
      isResizing = true;
      startX = e.pageX;
      startWidth = parseInt(window.getComputedStyle(col).width, 10);

      document.addEventListener("mousemove", resizeColumn);
      document.addEventListener("mouseup", stopResize);
    });

    const resizeColumn = (e) => isResizing && (col.style.width = `${startWidth + e.pageX - startX}px`);
    const stopResize = () => {
      document.removeEventListener("mousemove", resizeColumn);
      document.removeEventListener("mouseup", stopResize);
      isResizing = false;
    };
  });
}

// Reset the select element to default after status change
function resetSelectElement() {
  setTimeout(() => {
    const selectElement = document.querySelector('select');
    selectElement && (selectElement.value = '');
  });
}

// Reset selected issue and job after assigning
function resetSelections() {
  selectedIssue.value = undefined;
  selectedJob.value = undefined;
  jobComments.value = '';
}

// Open live viewer
function openLiveViewer() {
  isGcodeLiveViewVisible.value = true;
}

// Open image viewer
function openImageViewer() {
  isGcodeImageVisible.value = true;
  getFile(currentJob.value).then(file => {
    if (file) currentJob.value.file = file;
  });
}

// Return appropriate status text for the printer
const getStatusText = (printer: Device) => {
  return printer.status === 'printing' && printer.queue?.[0]?.released === 0 ? 'Waiting release' : printer.status;
};

// Define actions based on the printer's status
const printerActions = (printer: Device) => {
  const actions = [];
  if (['configuring', 'offline', 'error'].includes(printer.status)) {
    actions.push({ text: 'Set to Ready', class: 'btn btn-primary', method: () => setPrinterStatus(printer, 'ready') });
  }
  if (['configuring', 'ready', 'error', 'complete'].includes(printer.status)) {
    actions.push({ text: 'Turn Offline', class: 'btn btn-danger', method: () => setPrinterStatus(printer, 'offline') });
  }
  if (printer.status === 'printing' && printer.queue?.[0].released === 0) {
    actions.push({ text: 'Start Print', class: 'btn btn-secondary', method: () => startPrint(printer.id, printer.queue[0].id) });
  }
  return actions;
};
</script>

<template>
  <div class="container">
    <table ref="table">
      <tr>
        <th v-for="(header, index) in headers" :key="index" :style="header.style" class="resizable">
          {{ header.text }}
          <div class="resize-handle"></div>
        </th>
      </tr>
      <draggable v-model="printers" tag="tbody" :animation="300" item-key="printer.id" handle=".handle"
                 dragClass="hidden-ghost" @start="collapseAll" @end="restoreExpandedState">
        <template #item="{ element: printer }">
          <tr>
            <td>{{ printer.queue?.[0]?.td_id || 'idle' }}</td>
            <td class="truncate" :title="printer.name">{{ printer.name }}</td>
            <td>{{ getStatusText(printer) }}</td>
            <td class="truncate" :title="printer.queue?.[0]?.name">{{ printer.queue?.[0]?.name || '' }}</td>
            <td class="truncate" :title="printer.queue?.[0]?.file_name_original">{{ printer.queue?.[0]?.file_name_original || '' }}</td>
            <td>
              <div class="buttons">
                <button v-for="action in printerActions(printer)" :key="action.text" :class="action.class" @click="action.method">{{ action.text }}</button>
              </div>
            </td>
            <td>
              <div class="progress-wrapper">
                <div v-if="printer.queue?.[0]?.progress !== undefined" class="progress">
                  <div class="progress-bar" :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"></div>
                  <p class="progress-text">{{ printer.queue?.[0]?.progress?.toFixed(2) + '%' || '0.00%' }}</p>
                </div>
              </div>
            </td>
            <td style="width: 1%; white-space: nowrap;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <!-- Dropdown icon for actions -->
                <i :class="{ 'fa fa-chevron-down': !printer.isInfoExpanded, 'fa fa-chevron-up': printer.isInfoExpanded }"
                   @click="openPrinterInfo(printer)">
                </i>

                <!-- Dropdown actions for the printer -->
                <div :class="{ 'not-draggable': printer.queue && printer.queue.length === 0 }" class="dropdown">
                  <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                          style="background: none; border: none;">
                    <i class="fas fa-bars" :class="{ 'icon-disabled': printer.queue && printer.queue.length === 0 }"></i>
                  </button>
                  <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                    <!-- Display GCode Image if the printer has jobs -->
                    <li v-if="printer.queue && printer.queue.length > 0">
                      <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                         data-bs-target="#gcodeImageModal" v-bind:job="printer.queue[0]"
                         @click="openModal(printer.queue[0], printer.name, 2, printer)">
                        <i class="fa-solid fa-image"></i>
                        <span class="ms-2">GCode Image</span>
                      </a>
                    </li>
                    <!-- Display GCode Live if the printer has extruded job -->
                    <li v-if="printer.queue.length > 0 && printer.queue[0].extruded">
                      <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                         data-bs-target="#gcodeLiveViewModal" v-bind:job="printer.queue[0]"
                         @click="openModal(printer.queue[0], printer.name, 1, printer)">
                        <i class="fas fa-code"></i>
                        <span class="ms-2">GCode Live</span>
                      </a>
                    </li>
                    <!-- Display Download option -->
                    <li v-if="printer.queue.length > 0">
                      <a class="dropdown-item d-flex align-items-center" @click="getFileDownload(printer.queue[0].id)">
                        <i class="fas fa-download"></i>
                        <span class="ms-2">Download</span>
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </td>
            <td class="text-center handle"><i class="fas fa-grip-vertical"></i></td>
          </tr>
        </template>
      </draggable>
    </table>
    <div v-if="printers.length === 0" class="no-printers-message">
      No printers available. Either register a printer <RouterLink to="/registration">here</RouterLink>, or restart the server.
    </div>
  </div>

  <!-- Modals for GCode Image and Live View -->
  <div class="modal fade" id="gcodeLiveViewModal" tabindex="-1" aria-labelledby="gcodeLiveViewModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeLiveViewModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}<br>
            <b>Z-Layer:</b> {{ currentJob?.current_layer_height }}/{{ currentJob?.max_layer_height }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DLiveViewer v-if="isGcodeLiveViewVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true">
    <div :class="['modal-dialog', isImageVisible ? '' : 'modal-xl', 'modal-dialog-centered']">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeImageModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
            <div class="form-check form-switch">
              <label class="form-check-label" for="switchView">{{ isImageVisible ? 'Image' : 'Viewer' }}</label>
              <input class="form-check-input" type="checkbox" id="switchView" v-model="isImageVisible">
            </div>
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DImageViewer v-if="isGcodeImageVisible && !isImageVisible" :job="currentJob" />
            <GCodeThumbnail v-else-if="isGcodeImageVisible && isImageVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Resize handle styles */
.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  width: 5px;
  height: 100%;
  cursor: col-resize;
}

.resize-handle:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.resizable {
  border-right: 1px solid black;
}

table {
  table-layout: fixed;
  width: 100%;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.buttons {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.progress-wrapper {
  position: relative;
}

.progress-bar {
  width: 100%;
  height: 100%;
}

.progress-text {
  position: absolute;
  width: 100%;
  text-align: center;
  color: var(--color-background-font);
}

.text-center {
  text-align: center;
}

.no-printers-message {
  margin-top: 1rem;
}
</style>
