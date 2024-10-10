<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { printers, useSetStatus, useMovePrinterList, type Device } from '@/model/ports';
import { VueDraggableNext } from 'vue-draggable-next';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue';
import GCodeThumbnail from '@/components/GCodeThumbnail.vue';
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import { useAssignIssue, useGetIssues, type Issue } from '@/model/issues';
import { jobTime, useAssignComment, useGetFile, useGetJobFile, useReleaseJob, useStartJob, type Job } from '@/model/jobs';
import { useRouter, RouterLink } from 'vue-router';
import TableInfo from "@/components/TableInfo.vue";

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
const issuelist = ref<Array<Issue>>([]);
const isGcodeImageVisible = ref(false);
const isImageVisible = ref(true);
const isGcodeLiveViewVisible = ref(false);

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
  { text: 'Actions', style: 'width: 133px; position: relative;' },
];

// On component mount, fetch issues and initialize modals
onMounted(async () => {
  issuelist.value = await issues();
  setupModalEvents();
  initResizableColumns();
});

// Collapse and restore expanded printer state
const collapseAll = () => {
  expandedState = printers.value.filter(printer => printer.isInfoExpanded).map(printer => printer.id?.toString());
  printers.value.forEach(printer => (printer.isInfoExpanded = false));
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
  const table = document.querySelector('table');
  const cols = table?.querySelectorAll('th');
  let isResizing = false,
      startX,
      startWidth;

  cols?.forEach(col => {
    const resizer = col.querySelector('.resize-handle');

    resizer?.addEventListener('mousedown', e => {
      isResizing = true;
      startX = e.pageX;
      startWidth = parseInt(window.getComputedStyle(col).width, 10);

      document.addEventListener('mousemove', resizeColumn);
      document.addEventListener('mouseup', stopResize);
    });

    const resizeColumn = e => {
      if (isResizing) col.style.width = `${startWidth + e.pageX - startX}px`;
    };
    const stopResize = () => {
      document.removeEventListener('mousemove', resizeColumn);
      document.removeEventListener('mouseup', stopResize);
      isResizing = false;
    };
  });
}

// Reset the select element to default after status change
function resetSelectElement() {
  setTimeout(() => {
    const selectElement = document.querySelector('select');
    if (selectElement) selectElement.value = '';
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
</script>

<template>
  <div class="container">
    <table ref="table">
      <thead>
      <tr>
        <th
            v-for="(header, index) in headers"
            :key="index"
            :style="header.style"
            class="resizable"
        >
          {{ header.text }}
          <div class="resize-handle"></div>
        </th>
      </tr>
      </thead>
      <tbody>
      <VueDraggableNext v-model="printers" @end="handleDragEnd">
        <tr v-for="printer in printers" :key="printer.id">
          <TableInfo :printer="printer" :setPrinterStatus="setPrinterStatus" />
        </tr>
      </VueDraggableNext>
      </tbody>
    </table>
    <div v-if="printers.length === 0" class="no-printers-message">
      No printers available. Either register a printer
      <RouterLink to="/registration">here</RouterLink>
      , or restart the server.
    </div>

    <!-- Modals for GCode Image and Live View -->
    <div
        class="modal fade"
        id="gcodeLiveViewModal"
        tabindex="-1"
        aria-labelledby="gcodeLiveViewModalLabel"
        aria-hidden="true"
    >
      <div class="modal-dialog modal-dialog-centered modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="gcodeLiveViewModalLabel">
              <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}<br />
              <b>Z-Layer:</b> {{ currentJob?.current_layer_height }}/
              {{ currentJob?.max_layer_height }}
            </h5>
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <GCode3DLiveViewer
                  v-if="isGcodeLiveViewVisible"
                  :job="currentJob"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
        class="modal fade"
        id="gcodeImageModal"
        tabindex="-1"
        aria-labelledby="gcodeImageModalLabel"
        aria-hidden="true"
    >
      <div
          :class="[
          'modal-dialog',
          isImageVisible ? '' : 'modal-xl',
          'modal-dialog-centered',
        ]"
      >
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="gcodeImageModalLabel">
              <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
              <div class="form-check form-switch">
                <label class="form-check-label" for="switchView"
                >{{ isImageVisible ? 'Image' : 'Viewer' }}</label
                >
                <input
                    class="form-check-input"
                    type="checkbox"
                    id="switchView"
                    v-model="isImageVisible"
                />
              </div>
            </h5>
            <button
                type="button"
                class="btn-close"
                data-bs-dismiss="modal"
                aria-label="Close"
            ></button>
          </div>
          <div class="modal-body">
            <div class="row">
              <GCode3DImageViewer
                  v-if="isGcodeImageVisible && !isImageVisible"
                  :job="currentJob"
              />
              <GCodeThumbnail
                  v-else-if="isGcodeImageVisible && isImageVisible"
                  :job="currentJob"
              />
            </div>
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
  top: 0;
  right: 0;
  width: 5px;
  height: 100%;
  cursor: col-resize;
  background-color: transparent;
}

th:hover .resize-handle {
  background-color: var(--color-border);
}

.resizable {
  border-right: 1px solid black;
}

table {
  table-layout: fixed;
  border-collapse: collapse;
  width: 100%;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.buttons {
  display: flex;
  justify-content: center;
  align-content: center;
  flex-wrap: wrap;
}

.buttons button {
  margin: 0.25rem;
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

tr {
  display: table-row !important;
}

tbody {
  display: table-row-group !important;
  height: max-content;
}
</style>
