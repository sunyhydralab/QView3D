<script setup lang="ts">
import { nextTick, onMounted, ref, watchEffect } from 'vue';
import { printers, useSetStatus, useMovePrinterList, type Device } from '@/model/ports';
import draggable from 'vuedraggable'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCodeThumbnail from '@/components/GCodeThumbnail.vue';
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import { useAssignIssue, useGetIssues, type Issue } from '@/model/issues';
import { jobTime, useAssignComment, useGetFile, useGetJobFile, useReleaseJob, useStartJob, type Job } from '@/model/jobs';
import { useRouter } from 'vue-router';

const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { releaseJob } = useReleaseJob()
const { issues } = useGetIssues()
const { getFile } = useGetFile()
const { setStatus } = useSetStatus();
const { start } = useStartJob()
const { getFileDownload } = useGetJobFile()
const { movePrinterList } = useMovePrinterList()

const router = useRouter()

const selectedIssue = ref<Issue>()
const selectedJob = ref<Job>()
const jobComments = ref('')

const currentJob = ref<Job>();
const currentPrinter = ref<Device>();

const issuelist = ref<Array<Issue>>([])

const isGcodeImageVisible = ref(false)
const isImageVisible = ref(true)

const isGcodeLiveViewVisible = ref(false)

let expandedState: (string | undefined)[] = [];

onMounted(async () => {
  const retrieveissues = await issues()
  issuelist.value = retrieveissues

  const imageModal = document.getElementById('gcodeImageModal')

  imageModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeImageVisible.value = false;
    isImageVisible.value = true;
  });

  const liveModal = document.getElementById('gcodeLiveViewModal')

  liveModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeLiveViewVisible.value = false;
  });
});

function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60)
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

  const hoursStr = hours < 10 ? '0' + hours : hours
  const minutesStr = minutes < 10 ? '0' + minutes : minutes
  const secondsStr = seconds < 10 ? '0' + seconds : seconds

  if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN' || hoursStr + ':' + minutesStr + ':' + secondsStr === '00:00:00')) return '<i>Waiting...</i>'
  return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds)
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })

  if (isNaN(milliseconds) || isNaN(date.getTime()) || timeString === "07:00 PM" || timeString === "07:00:00 PM") {
    return '<i>Waiting...</i>'
  }

  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

const collapseAll = () => {
  expandedState = printers.value.filter(printer => printer.isInfoExpanded).map(printer => printer.id?.toString());
  printers.value.forEach(printer => printer.isInfoExpanded = false);
}

const restoreExpandedState = () => {
  printers.value.forEach(printer => {
    if (expandedState.includes(printer.id?.toString())) {
      printer.isInfoExpanded = true;
    }
  });
}

const doAssignIssue = async () => {
  if (selectedJob.value === undefined) return
  await assignComment(selectedJob.value, jobComments.value)
  await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid)

  if (selectedIssue.value !== undefined) {
    await assign(selectedIssue.value.id, selectedJob.value.id)
  }

  selectedJob.value.comments = jobComments.value
  selectedIssue.value = undefined
  selectedJob.value = undefined

  await nextTick()
}

const openModal = async (job: Job, printerName: string, num: number, printer: Device) => {
  await jobTime(job, printers)
  currentJob.value = job
  currentJob.value.printer = printerName
  currentPrinter.value = printer
  if (num == 1) {
    isGcodeLiveViewVisible.value = true
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

const setJob = async (job: Job) => {
  jobComments.value = job.comments || '';
  selectedJob.value = job;
}

const sendToQueueView = (printer: Device | undefined) => {
  if (printer) {
    printer.isQueueExpanded = true;
    router.push({ name: 'QueueViewVue' });
  }
}

const setPrinterStatus = async (printer: Device, status: string) => {
  await setStatus(printer.id, status); // update the status in the backend
  setTimeout(() => {
    // Using setTimeout to ensure the value is reset after the change event is processed
    const selectElement = document.querySelector('select');
    if (selectElement) {
      (selectElement as HTMLSelectElement).value = '';
    }
  });
}

const startPrint = async (printerid: number, jobid: number) => {
  await start(jobid, printerid)
}

const openPrinterInfo = async (printer: Device) => {
  if (printer.queue && printer.queue[0]) {
    await jobTime(printer.queue[0], printers)
  }

  printer.isInfoExpanded = !printer.isInfoExpanded;

}

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {

  let printer = printers.value.find((printer) => printer.id === printerIdToPrintTo)
  printer!.error = ""

  if (printer) {
    printer.extruder_temp = 0
    printer.bed_temp = 0;
  }

  await releaseJob(jobToFind, key, printerIdToPrintTo)
  await nextTick()
}

const handleDragEnd = async () => {
  await movePrinterList(printers.value)
}

</script>

<template>

  <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
    data-bs-backdrop="static">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header d-flex align-items-end">
          <h5 class="modal-title mb-0" id="assignIssueLabel" style="line-height: 1;">
            Job #{{ selectedJob?.td_id }}</h5>
          <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px; line-height: 1;">
            {{ selectedJob?.date }}</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
            @click="selectedIssue = undefined; selectedJob = undefined;"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="">
            <div class="mb-3">
              <label for="issue" class="form-label">Select Issue</label>
              <select name="issue" id="issue" v-model="selectedIssue" class="form-select" required>
                <option disabled value="undefined">Select Issue</option>
                <option v-for="issue in issuelist" :value="issue">
                  {{ issue.issue }}
                </option>
              </select>
            </div>
          </form>
          <div class="form-group mt-3">
            <label for="exampleFormControlTextarea1">Comments</label>
            <textarea class="form-control" id="exampleFormControlTextarea1" rows="3" v-model="jobComments"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
            @click="selectedIssue = undefined; selectedJob = undefined">Close</button>
          <button type="button" class="btn btn-success" data-bs-dismiss="modal" @click="doAssignIssue">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeLiveViewModal' -->
  <div class="modal fade" id="gcodeLiveViewModal" tabindex="-1" aria-labelledby="gcodeLiveViewModalLaebl"
    aria-hidden="true">
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

  <!-- bootstrap 'gcodeImageModal' -->
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
            <GCode3DImageViewer v-if="isGcodeImageVisible && !isImageVisible" :job="currentJob" />
            <GCodeThumbnail v-else-if="isGcodeImageVisible && isImageVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="container">
    <table ref="table">
      <tr>
        <!-- NEED TO FIX THIS FOR EVERY DISPLAYS -->
        <th style="width: 64px">ID</th>
        <th style="width: 130px">Printer name</th>
        <th style="width: 142px">Printer Status</th>
        <th style="width: 110px">Job Name</th>
        <th style="width: 110px">File</th>
        <th style="width: 314px">Printer Options</th>
        <th style="width: 315px">Progress</th>
        <th style="width: 75px;">Actions</th>
        <th style="width: 58px">Move</th>
      </tr>
      <draggable v-model="printers" tag="tbody" :animation="300" item-key="printer.id" handle=".handle"
        dragClass="hidden-ghost" :onEnd="handleDragEnd" v-if="printers.length > 0" @start="collapseAll"
        @end="restoreExpandedState">
        <template #item="{ element: printer }">
          <div v-if="printer.isInfoExpanded" class="expanded-info">
            <tr :id="printer.id">
              <td
                v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
                {{ printer.queue?.[0].td_id }}
              </td>
              <td v-else><i>idle</i></td>

              <td class="truncate" :title="printer.name">
                <button type="button" class="btn btn-link" @click="sendToQueueView(printer)"
                  style="padding: 0; border: none; display: inline-block; width: 100%; text-align: center;">
                  <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                    {{ printer.name }}
                  </div>
                </button>
              </td>

              <td>
                <div class="d-flex align-items-center justify-content-center">
                  <!-- <p class="mb-0 me-2" v-if="printer.status === 'colorchange'" style="color: red">
                Change filament
              </p> -->
                  <p v-if="printer.status === 'printing' && printer.queue?.[0]?.released === 0" style="color: #ad6060"
                    class="mb-0 me-2">
                    Waiting release
                  </p>
                  <p v-else class="mb-0 me-2">
                    {{ printer.status }}
                  </p>
                </div>
              </td>

              <td class="truncate" :title="printer.queue?.[0]?.name"
                v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
                {{ printer.queue?.[0]?.name }}
              </td>
              <td v-else></td>

              <td class="truncate" :title="printer.queue?.[0]?.file_name_original"
                v-if="(printer.queue && printer.queue.length > 0 && (printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange') || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
                {{ printer.queue?.[0]?.file_name_original }}
              </td>
              <td v-else></td>

              <td>
                <div class="buttons">

                  <button class="btn btn-primary"
                    v-if="printer.status == 'configuring' || printer.status == 'offline' || printer.status == 'error'"
                    @click="setPrinterStatus(printer, 'ready')">
                    Set to Ready
                  </button>

                  <button class="btn btn-danger"
                    v-if="printer.status == 'configuring' || printer.status == 'ready' || printer.status == 'error' || printer.status == 'complete'"
                    @click="setPrinterStatus(printer, 'offline')">
                    Turn Offline
                  </button>

                  <button class="btn btn-success"
                    v-if="printer.status == 'printing' && printer.queue?.[0].released == 0"
                    @click="startPrint(printer.id, printer.queue[0].id)">
                    Start Print
                  </button>

                  <button class="btn btn-success" :disabled="printer.queue?.[0]?.extruded == 0"
                    @click="setPrinterStatus(printer, 'paused')"
                    v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                    Pause
                  </button>

                  <button class="btn btn-success" :disabled="printer.queue?.[0]?.extruded == 0"
                    @click="setPrinterStatus(printer, 'colorchange')"
                    v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                    Color&nbsp;Change
                  </button>

                  <button class="btn btn-secondary" @click="setPrinterStatus(printer, 'printing')"
                    v-if="printer.status == 'paused'">
                    Unpause
                  </button>

                  <button class="btn btn-danger" @click="setPrinterStatus(printer, 'complete')"
                    v-if="(printer.status == 'printing' || printer.status == 'colorchange')">
                    Stop
                  </button>

                  <div
                    v-if="printer.status == 'colorchange' && (printer.colorbuff == 1 || printer.queue[0].file_pause == 1)"
                    class="mt-2">
                    Ready for color change.
                  </div>
                  <div v-else-if="printer.status == 'colorchange' && printer.queue[0].file_pause == 0" class="mt-2">
                    Finishing current layer...
                  </div>

                </div>
              </td>

              <td style="width: 250px;">
                <div
                  v-if="(printer.status === 'printing' || printer.status == 'paused' || printer.status == 'colorchange') && printer.queue && printer.queue[0].released == 1">
                  <!-- <div v-for="job in printer.queue" :key="job.id"> -->
                  <!-- Display the elapsed time -->
                  <div class="progress" style="position: relative;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                      :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"
                      :aria-valuenow="printer.queue?.[0].progress" aria-valuemin="0" aria-valuemax="100">
                    </div>
                    <!-- job progress set to 2 decimal places -->
                    <p style="position: absolute; width: 100%; text-align: center; color: black;">{{
              printer.queue?.[0].progress
                ?
                `${printer.queue?.[0].progress.toFixed(2)}%` : '0.00%' }}</p>
                  </div>
                  <!-- </div> -->
                </div>

                <div
                  v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'complete' || printer.queue?.[0].status == 'cancelled')">
                  <div class="buttons-progress">
                    <div type="button" class="btn btn-secondary"
                      @click="releasePrinter(printer.queue?.[0], 1, printer.id)">
                      Clear
                    </div>
                    <div class="btn-group">
                      <div class="btn btn-primary no-wrap" @click="releasePrinter(printer.queue?.[0], 2, printer.id)">
                        Clear/Rerun
                      </div>
                      <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                        aria-expanded="false">
                      </div>
                      <div class="dropdown-menu">
                        <div class="dropdown-item" v-for="printer in printers" :key="printer.id"
                          @click="releasePrinter(printer.queue?.[0], 2, printer.id!)">
                          {{ printer.name }}
                        </div>
                      </div>
                    </div>
                    <div type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#issueModal"
                      @click=setJob(printer.queue[0])>
                      Fail
                    </div>
                  </div>
                </div>

                <div
                  v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'printing' && printer.status == 'complete')">
                  <div style="display: flex; justify-content: center; align-items: center;">
                    <button class="btn btn-primary w-100" type="button" disabled>
                      <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                      <span class="sr-only">Finishing print...</span>
                    </button>
                  </div>
                </div>
                <div v-else-if="printer.status == 'error'" class="alert alert-danger truncate" role="alert">
                  {{ printer?.error }}
                </div>
                <div v-else></div>

              </td>

              <td style="width: 1%; white-space: nowrap;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <i :class="{ 'fa fa-chevron-down': !printer.isInfoExpanded, 'fa fa-chevron-up': printer.isInfoExpanded }"
                    @click="openPrinterInfo(printer)">
                  </i>
                  <div :class="{ 'not-draggable': printer.queue && printer.queue.length == 0 }" class="dropdown">
                    <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                      <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                        style="background: none; border: none;">
                        <i class="fa-solid fa-bars"
                          :class="{ 'icon-disabled': printer.queue && printer.queue.length == 0 }"></i>
                      </button>
                      <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                        <li>
                          <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                            data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                            v-bind:job="printer.queue[0]"
                            @click="printer.name && openModal(printer.queue[0], printer.name, 2, printer)">
                            <i class="fa-solid fa-image"></i>
                            <span class="ms-2">GCode Image</span>
                          </a>
                        </li>
                        <li v-if="printer.queue.length > 0 && (printer.queue[0] && printer.queue[0].extruded)">
                          <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                            data-bs-target="#gcodeLiveViewModal" v-if="printer.queue && printer.queue.length > 0"
                            v-bind:job="printer.queue[0]"
                            @click="printer.name && openModal(printer.queue[0], printer.name, 1, printer)">
                            <i class="fas fa-code"></i>
                            <span class="ms-2">GCode Live</span>
                          </a>
                        </li>
                        <li v-if="printer.queue[0]">
                          <a class="dropdown-item d-flex align-items-center"
                            @click="getFileDownload(printer.queue[0].id)"
                            :disabled="printer.queue[0].file_name_original.includes('.gcode:')">
                            <i class="fas fa-download"></i>
                            <span class="ms-2">Download</span>
                          </a>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>
              </td>

              <td class="text-center handle"
                :class="{ 'not-draggable': printers.length <= 1 || printer.isInfoExpanded }"
                :style="{ 'vertical-align': printer.isInfoExpanded ? 'middle' : '' }">
                <i class="fas fa-grip-vertical"
                  :class="{ 'icon-disabled': printers.length <= 1 || printer.isInfoExpanded }"></i>
              </td>
            </tr>
            <tr style="background-color: #cdcdcd;">
              <td class="borderless-bottom">
                <b>Layer:</b>
              </td>
              <td class="borderless-bottom">
                <b>Filament:</b>
              </td>
              <td class="borderless-bottom">
                <b>Nozzle:</b>
              </td>
              <td class="borderless-bottom">
                <b>Bed:</b>
              </td>
              <td class="borderless-bottom">
                <b>Elapsed:</b>
              </td>
              <td class="borderless-bottom">
                <b>Remaining:</b>
              </td>
              <td class="borderless-bottom">
                <b>Total:</b>
              </td>
              <td class="borderless-bottom" colspan="2">
                <b>ETA:</b>
              </td>
            </tr>
            <tr style="background-color: #cdcdcd;">
              <td class="borderless-top">
                <span
                  v-if="printer.queue[0] && printer.queue[0]?.current_layer_height != null && printer.queue[0]?.max_layer_height != null && printer.queue[0]?.max_layer_height !== 0">
                  {{ printer.queue[0]?.current_layer_height + '/' + printer.queue[0]?.max_layer_height }}
                </span>
                <span v-else>
                  <i>idle</i>
                </span>
              </td>
              <td class="borderless-top">
                <span v-html="printer.queue[0]?.filament ? printer.queue[0]?.filament : '<i>idle</i>'"></span>
              </td>
              <td class="borderless-top">
                <span v-html="printer?.extruder_temp ? printer.extruder_temp + '&deg;C' : '<i>idle</i>'"></span>
              </td>
              <td class="borderless-top">
                <span v-html="printer?.bed_temp ? printer.bed_temp + '&deg;C' : '<i>idle</i>'"></span>
              </td>
              <td class="borderless-top">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.elapsed_time)"></span>
              </td>
              <td class="borderless-top">
                <span v-if="printer.queue[0]?.job_client?.remaining_time !== 0"
                  v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.remaining_time)"></span>
                <span v-else v-html="'00:00:00'"></span>
              </td>
              <td class="borderless-top">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.total_time)"></span>
              </td>
              <td class="borderless-top" colspan="2">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting...' : (printer.queue[0]?.extruded ? formatETA(printer.queue[0]?.job_client?.eta) : '<i>Waiting...</i>')"></span>
              </td>
            </tr>
          </div>
          <tr v-else :id="printer.id">
            <td
              v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
              {{ printer.queue?.[0].td_id }}
            </td>
            <td v-else><i>idle</i></td>

            <td class="truncate" :title="printer.name">
              <button type="button" class="btn btn-link" @click="sendToQueueView(printer)"
                style="padding: 0; border: none; display: inline-block; width: 100%; text-align: center;">
                <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  {{ printer.name }}
                </div>
              </button>
            </td>

            <td>
              <div class="d-flex align-items-center justify-content-center">
                <!-- <p class="mb-0 me-2" v-if="printer.status === 'colorchange'" style="color: red">
                Change filament
              </p> -->
                <p v-if="printer.status === 'printing' && printer.queue?.[0]?.released === 0" style="color: #ad6060"
                  class="mb-0 me-2">
                  Waiting release
                </p>
                <p v-else class="mb-0 me-2">
                  {{ printer.status }}
                </p>
              </div>
            </td>

            <td class="truncate" :title="printer.queue?.[0]?.name"
              v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
              {{ printer.queue?.[0]?.name }}
            </td>
            <td v-else></td>

            <td class="truncate" :title="printer.queue?.[0]?.file_name_original"
              v-if="(printer.queue && printer.queue.length > 0 && (printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange') || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
              {{ printer.queue?.[0]?.file_name_original }}
            </td>
            <td v-else></td>

            <td>
              <div class="buttons">

                <button class="btn btn-primary"
                  v-if="printer.status == 'configuring' || printer.status == 'offline' || printer.status == 'error'"
                  @click="setPrinterStatus(printer, 'ready')">
                  Set to Ready
                </button>

                <button class="btn btn-danger"
                  v-if="printer.status == 'configuring' || printer.status == 'ready' || printer.status == 'error' || printer.status == 'complete'"
                  @click="setPrinterStatus(printer, 'offline')">
                  Turn Offline
                </button>

                <button class="btn btn-success" v-if="printer.status == 'printing' && printer.queue?.[0].released == 0"
                  @click="startPrint(printer.id, printer.queue[0].id)">
                  Start Print
                </button>

                <button class="btn btn-success" :disabled="printer.queue?.[0]?.extruded == 0"
                  @click="setPrinterStatus(printer, 'paused')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                  Pause
                </button>

                <button class="btn btn-success" :disabled="printer.queue?.[0]?.extruded == 0"
                  @click="setPrinterStatus(printer, 'colorchange')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                  Color&nbsp;Change
                </button>

                <button class="btn btn-secondary" @click="setPrinterStatus(printer, 'printing')"
                  v-if="printer.status == 'paused'">
                  Unpause
                </button>

                <button class="btn btn-danger" @click="setPrinterStatus(printer, 'complete')"
                  v-if="(printer.status == 'printing' || printer.status == 'colorchange')">
                  Stop
                </button>

                <div
                  v-if="printer.status == 'colorchange' && (printer.colorbuff == 1 || printer.queue[0].file_pause == 1)"
                  class="mt-2">
                  Ready for color change.
                </div>
                <div v-else-if="printer.status == 'colorchange' && printer.queue[0].file_pause == 0" class="mt-2">
                  Finishing current layer...
                </div>

              </div>
            </td>

            <td style="width: 250px;">
              <div
                v-if="(printer.status === 'printing' || printer.status == 'paused' || printer.status == 'colorchange') && printer.queue && printer.queue[0].released == 1">
                <!-- <div v-for="job in printer.queue" :key="job.id"> -->
                <!-- Display the elapsed time -->
                <div class="progress" style="position: relative;">
                  <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                    :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"
                    :aria-valuenow="printer.queue?.[0].progress" aria-valuemin="0" aria-valuemax="100">
                  </div>
                  <!-- job progress set to 2 decimal places -->
                  <p style="position: absolute; width: 100%; text-align: center; color: black;">{{
              printer.queue?.[0].progress
                ?
                `${printer.queue?.[0].progress.toFixed(2)}%` : '0.00%' }}</p>
                </div>
                <!-- </div> -->
              </div>

              <div
                v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'complete' || printer.queue?.[0].status == 'cancelled')">
                <div class="buttons-progress">
                  <div type="button" class="btn btn-secondary"
                    @click="releasePrinter(printer.queue?.[0], 1, printer.id)">
                    Clear
                  </div>
                  <div class="btn-group">
                    <div class="btn btn-primary no-wrap" @click="releasePrinter(printer.queue?.[0], 2, printer.id)">
                      Clear/Rerun
                    </div>
                    <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                      aria-expanded="false">
                    </div>
                    <div class="dropdown-menu">
                      <div class="dropdown-item" v-for="printer in printers" :key="printer.id"
                        @click="releasePrinter(printer.queue?.[0], 2, printer.id!)">
                        {{ printer.name }}
                      </div>
                    </div>
                  </div>
                  <div type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#issueModal"
                    @click=setJob(printer.queue[0])>
                    Fail
                  </div>
                </div>
              </div>

              <div
                v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'printing' && printer.status == 'complete')">
                <div style="display: flex; justify-content: center; align-items: center;">
                  <button class="btn btn-primary w-100" type="button" disabled>
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    <span class="sr-only">Finishing print...</span>
                  </button>
                </div>
              </div>
              <div v-else-if="printer.status == 'error'" class="alert alert-danger truncate" role="alert"
                :title="printer?.error">
                {{ printer?.error }}
              </div>
              <div v-else></div>

            </td>

            <td style="width: 1%; white-space: nowrap;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <i :class="{ 'fa fa-chevron-down': !printer.isInfoExpanded, 'fa fa-chevron-up': printer.isInfoExpanded }"
                  @click="openPrinterInfo(printer)">
                </i>
                <div :class="{ 'not-draggable': printer.queue && printer.queue.length == 0 }" class="dropdown">
                  <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                    <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                      style="background: none; border: none;">
                      <i class="fa-solid fa-bars"
                        :class="{ 'icon-disabled': printer.queue && printer.queue.length == 0 }"></i>
                    </button>
                    <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                      <li>
                        <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                          data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                          v-bind:job="printer.queue[0]"
                          @click="printer.name && openModal(printer.queue[0], printer.name, 2, printer)">
                          <i class="fa-solid fa-image"></i>
                          <span class="ms-2">GCode Image</span>
                        </a>
                      </li>
                      <li v-if="printer.queue.length > 0 && (printer.queue[0] && printer.queue[0].extruded)">
                        <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                          data-bs-target="#gcodeLiveViewModal" v-if="printer.queue && printer.queue.length > 0"
                          v-bind:job="printer.queue[0]"
                          @click="printer.name && openModal(printer.queue[0], printer.name, 1, printer)">
                          <i class="fas fa-code"></i>
                          <span class="ms-2">GCode Live</span>
                        </a>
                      </li>
                      <li v-if="printer.queue[0]">
                        <a class="dropdown-item d-flex align-items-center" @click="getFileDownload(printer.queue[0].id)"
                          :disabled="printer.queue[0].file_name_original.includes('.gcode:')">
                          <i class="fas fa-download"></i>
                          <span class="ms-2">Download</span>
                        </a>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </td>

            <td class="text-center handle" :class="{ 'not-draggable': printers.length <= 1 || printer.isInfoExpanded }"
              :style="{ 'vertical-align': printer.isInfoExpanded ? 'middle' : '' }">
              <i class="fas fa-grip-vertical"
                :class="{ 'icon-disabled': printers.length <= 1 || printer.isInfoExpanded }"></i>
            </td>
          </tr>
        </template>
      </draggable>
    </table>
    <div v-if="printers.length === 0" style="margin-top: 1rem;">
      No printers available. Either register a printer <RouterLink class="routerLink" to="/registration">here
      </RouterLink>,
      or restart the
      server.
    </div>
  </div>
</template>

<style scoped>
.borderless-bottom {
  border-bottom: none !important;
  line-height: 11.5px;
}

.borderless-top {
  border-top: none !important;
  line-height: 10px;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

table {
  table-layout: fixed;
}

th {
  user-select: none;
}

.expanded-info {
  display: contents;
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

.buttons>* {
  flex: 1 0 auto;
  margin: 0 0.375rem;
  flex-shrink: 0;
}


.dropdown-item {
  display: flex;
  align-items: center;
  padding-left: .5rem;
}

.dropdown-item i {
  width: 20px;
}

.dropdown-item span {
  margin-left: 10px;
}

.icon-disabled {
  color: #6e7073;
}

.not-draggable {
  pointer-events: none;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.hidden-ghost {
  opacity: 0;
}

.buttons-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.buttons-progress>* {
  margin: 0 0.375rem;
}

.no-wrap {
  white-space: nowrap;
}

.form-control {
  background: #f4f4f4;
  border: 1px solid #484848;
}

.form-select {
  background-color: #f4f4f4 !important;
  border-color: #484848 !important;
}

.alert {
  margin: 0;
  padding: 0.3rem;
}
</style>