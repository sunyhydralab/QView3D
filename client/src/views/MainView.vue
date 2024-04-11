<script setup lang="ts">
import { useSetStatus, type Device, printers } from '@/model/ports';
import { type Issue, useGetIssues, useCreateIssues, useAssignIssue } from '../model/issues'
import { type Job, useReleaseJob, useStartJob, useRemoveJob, useGetFile, jobTime, useAssignComment } from '@/model/jobs';
import { useRouter } from 'vue-router';
import { onMounted, ref } from 'vue';
import draggable from 'vuedraggable'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import HoldButton from '@/components/HoldButton.vue';

const { setStatus } = useSetStatus();
const { releaseJob } = useReleaseJob()
const { removeJob } = useRemoveJob()
const { getFile } = useGetFile()
const { start } = useStartJob()
const { issues } = useGetIssues()
const { createIssue } = useCreateIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()

const router = useRouter();
let currentJob = ref<Job>();
let currentPrinter = ref<Device>();
const selectedJob = ref<Job>()
const selectedIssue = ref<Issue>()
const showText = ref(false)
const newIssue = ref('')
let issuelist = ref<Array<Issue>>([])

let isGcodeImageVisible = ref(false)
let isGcodeLiveViewVisible = ref(false)
let jobComments = ref('')

onMounted(async () => {
  const retrieveissues = await issues()
  issuelist.value = retrieveissues
})

const sendToQueueView = (printer: Device | undefined) => {
  if (printer) {
    printer.isExpanded = true;
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

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {
  await releaseJob(jobToFind, key, printerIdToPrintTo)
}

function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60)
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

  const hoursStr = hours < 10 ? '0' + hours : hours
  const minutesStr = minutes < 10 ? '0' + minutes : minutes
  const secondsStr = seconds < 10 ? '0' + seconds : seconds

  if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN')) return 'Printer calibrating...'
  return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds)
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })


  if (isNaN(date.getTime()) || timeString === "07:00 PM") {
    return 'Printer calibrating...'
  }

  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
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

const startPrint = async (printerid: number, jobid: number) => {
  await start(jobid, printerid)
}

const setJob = async (job: Job) => {
  console.log("here")
  jobComments.value = job.comment || '';
  selectedJob.value = job;
}

const doCreateIssue = async () => {
  await createIssue(newIssue.value)
  const newIssues = await issues()
  console.log(newIssues)
  issuelist.value = newIssues
  newIssue.value = ''
  showText.value = false
}

const doAssignIssue = async () => {
  if (selectedJob.value === undefined) return
  await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid)

  if (selectedIssue.value !== undefined) {
    await assign(selectedIssue.value.id, selectedJob.value.id)
  }
  await assignComment(selectedJob.value, jobComments.value)
  selectedJob.value.comment = jobComments.value
  selectedIssue.value = undefined
  selectedJob.value = undefined
}
</script>

<template>


  <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
    data-bs-backdrop="static">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header d-flex align-items-end">
          <h5 class="modal-title mb-0" id="assignIssueLabel" style="line-height: 1;">Job #{{ selectedJob?.id
            }}</h5>
          <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px; line-height: 1;">{{
            selectedJob?.date }}</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
            @click="selectedIssue = undefined; selectedJob = undefined;"></button>
        </div>
        <div class="modal-body">
          <button class="btn btn-primary mb-3" @click="showText = !showText">Create New Issue</button>
          <form v-if="showText" class="p-3 border rounded bg-light mb-3">
            <div class="mb-3">
              <label for="newIssue" class="form-label">Enter Issue</label>
              <input id="newIssue" v-model="newIssue" type="text" placeholder="Enter Issue" class="form-control"
                required>
            </div>
            <div>
              <button type="submit" @click.prevent="doCreateIssue" class="btn btn-primary me-2"
                v-bind:disabled="!newIssue">Submit</button>
              <button @click.prevent="showText = !showText" class="btn btn-secondary">Cancel</button>
            </div>
          </form>
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
          <div v-if="selectedIssue !== undefined" class="alert alert-danger mt-3">
            Warning: Assigning an issue to a job in Job History will set the job status to Error and remove
            it from any active print queues. Please ensure that the job has been completed before assigning
            an issue.
          </div>
          <div class="form-group mt-3">
            <label for="exampleFormControlTextarea1">Comments</label>
            <textarea class="form-control" id="exampleFormControlTextarea1" rows="3" v-model="jobComments"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
            @click="selectedIssue = undefined; selectedJob = undefined">Close</button>
          <button type="button" class="btn btn-success" data-bs-dismiss="modal" @click="doAssignIssue">Save
            Changes</button>
        </div>
      </div>
    </div>
  </div>



  <!-- bootstrap 'infoModal' -->
  <div class="modal fade" id="infoModal" tabindex="-1" aria-labelledby="infoModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="infoModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <!-- Display other attributes of the job -->
          <div class="row">
            <div class="col-sm-12">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <h5 class="card-title"><i class="fas fa-chart-line"></i> <b>Progress:</b> {{ currentJob?.progress ?
                    `${currentJob?.progress.toFixed(2)}%` : '0.00%' }}</h5>
                  <div class="progress">
                    <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                      :style="{ width: `${currentJob?.progress ? currentJob?.progress.toFixed(2) : '0'}%` }"
                      aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="row">
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-hourglass-half"></i> <b>Elapsed Time:</b></h5>
                    </div>
                    <!-- <div class="col-12">{{ formatTime(currentJob?.job_client?.elapsed_time!) }}</div> -->
                    <div class="col-12">
                      {{ currentPrinter?.status === 'colorchange' ? 'Waiting for filament change...' :
                        formatTime(currentJob?.job_client?.elapsed_time!) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-hourglass-end"></i> <b>Remaining Time:</b></h5>
                    </div>
                    <!-- <div class="col-12">{{ formatTime(currentJob?.job_client?.remaining_time!) }}</div> -->
                    <div class="col-12">
                      {{ currentPrinter?.status === 'colorchange' ? 'Waiting for filament change...' :
                        formatTime(currentJob?.job_client?.remaining_time!) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-stopwatch"></i> <b>Total Time:</b></h5>
                    </div>
                    <div class="col-12">
                      <div v-if="currentPrinter?.status === 'colorchange'">
                        Waiting for filament change...
                      </div>
                      <div v-else>
                        <div v-if="currentJob?.job_client?.extra_time">
                          {{ formatTime(currentJob?.job_client.total_time!) + ' + ' +
                            formatTime(currentJob?.job_client.extra_time!) }}
                        </div>
                        <div v-else>
                          {{ formatTime(currentJob?.job_client?.total_time!) }}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-sm-3">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <div class="row">
                    <div class="col-12">
                      <h5 class="card-title"><i class="fas fa-stopwatch"></i> <b>ETA:</b></h5>
                    </div>
                    <!-- <div class="col-12">{{ formatETA(currentJob?.job_client?.eta!) ?? "Waiting to start heating..."  }}</div> -->
                    <div class="col-12">
                      {{ currentPrinter?.status === 'colorchange' ? 'Waiting for filament change...' :
                        formatETA(currentJob?.job_client?.eta!) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="row">
            <div class="col-sm-12 col-md-6">
              <div class="card bg-light mb-3 h-100">
                <div class="card-body">
                  <h5 class="card-title"><i class="fas fa-file-alt"></i> <b>Job ID:</b> {{ currentJob?.id }}</h5>
                  <h5 class="card-title"><i class="fas fa-clock"></i> <b>Job Status:</b> {{ currentJob?.status }}</h5>
                  <h5 class="card-title"><i class="fas fa-file"></i> <b>File Name:</b> {{ currentJob?.file_name_original
                    }}</h5>
                </div>
              </div>
            </div>
            <div class="col-sm-12 col-md-6">
              <div class="card bg-light mb-3 h-100">
                <div class="card-body">
                  <h5 class="card-title">
                    <i class="fas fa-thermometer-full"></i>
                    <b>Nozzle Temp: </b>
                    <span
                      v-html="currentPrinter?.extruder_temp ? currentPrinter.extruder_temp + '&deg;C' : '<i>idle</i>'"></span>
                  </h5>
                  <h5 class="card-title">
                    <i class="fas fa-thermometer-half"></i>
                    <b>Bed Temp: </b>
                    <span v-html="currentPrinter?.bed_temp ? currentPrinter.bed_temp + '&deg;C' : '<i>idle</i>'"></span>
                  </h5>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeLiveViewModal' -->
  <div class="modal fade" id="gcodeLiveViewModal" tabindex="-1" aria-labelledby="gcodeLiveViewModalLaebl"
    aria-hidden="true" @shown.bs.modal="isGcodeLiveViewVisible = true"
    @hidden.bs.modal="isGcodeLiveViewVisible = false">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeLiveViewModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
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
  <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true"
    @shown.bs.modal="isGcodeImageVisible = true" @hidden.bs.modal="isGcodeImageVisible = false">
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
            <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeModal' -->
  <div class="modal fade" id="gcodeModal" tabindex="-1" aria-labelledby="gcodeModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class=" row">
            <div class="col-sm-12">
              <div class="card bg-light mb-3">
                <div class="card-body">
                  <h5 class="card-title">
                    <pre> .GCODE VIEWER </pre>
                  </h5>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>


  <div class="container">
    <!-- <b>Home</b> -->
    <table class="table-striped">
      <tr>
        <!-- NEED TO FIX THIS FOR EVERY DISPLAYS -->
        <th style="width: 64px">Job ID</th>
        <th style="width: 130px">Printer name</th>
        <th style="width: 110px">Job Name</th>
        <th style="width: 110px">File</th>
        <th style="width: 142px">Printer Status</th>
        <th style="width: 314px">Printer Options</th>
        <th style="width: 315px">Progress</th>
        <th style="width: 75px;">Actions</th>
        <th style="width: 58px">Move</th>
      </tr>
      <draggable v-model="printers" tag="tbody" :animation="300" item-key="printer.id" handle=".handle"
        dragClass="hidden-ghost" v-if="printers.length > 0">
        <template #item="{ element: printer }">
          <tr :id="printer.id">
            <td
              v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
              {{ printer.queue?.[0].id }}
            </td>
            <td v-else><i>idle</i></td>
            <td class="truncate" :title="printer.name">
              <button type="button" class="btn btn-link" @click="sendToQueueView(printer)"
                style="padding: 0; border: none; display: inline-block; width: 100%; text-align: left;">
                <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                  {{ printer.name }}
                </div>
              </button>
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
              <div class="d-flex align-items-center justify-content-center">
                <!-- <p class="mb-0 me-2" v-if="printer.status === 'colorchange'" style="color: red">
                    Change filament
                  </p> -->
                <p v-if="printer.status === 'printing' && printer.queue?.[0]?.released === 0" style="color: red"
                  class="mb-0 me-2">
                  Waiting release
                </p>
                <p v-else class="mb-0 me-2">
                  {{ printer.status }}
                </p>
              </div>
            </td>

            <td>
              <div class="buttons">

                <button class="btn btn-primary"
                  v-if="printer.status == 'configuring' || printer.status == 'ready' || printer.status == 'error' || printer.status == 'complete'"
                  @click="setPrinterStatus(printer, 'offline')">
                  Turn Offline
                </button>

                <button class="btn btn-primary"
                  v-if="printer.status == 'configuring' || printer.status == 'offline' || printer.status == 'error'"
                  @click="setPrinterStatus(printer, 'ready')">
                  Set to Ready
                </button>

                <HoldButton :color="'success'" @button-held="startPrint(printer.id!, printer.queue?.[0].id)"
                  v-if="printer.status == 'printing' && printer.queue?.[0].released == 0">
                  Start Print
                </HoldButton>

                <HoldButton :color="'danger'" @button-held="setPrinterStatus(printer, 'complete')"
                  v-if="(printer.status == 'printing' || printer.status == 'colorchange')">
                  Stop
                </HoldButton>

                <!-- <HoldButton :disabled="printer.queue?.[0]?.extruded" :color="'warning'"
                  @button-held="setPrinterStatus(printer, 'paused')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0) && printer.queue?.[0]?.extruded === 1">
                  Pause
                </HoldButton>

                <HoldButton :disabled="printer.queue?.[0]?.extruded" :color="'warning'"
                  @button-held="setPrinterStatus(printer, 'colorchange')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0) && printer.queue?.[0]?.extruded === 1">
                  Color&nbsp;Change
                </HoldButton> -->

                <HoldButton :disabled="printer.queue?.[0]?.extruded" :color="'warning'"
                  @button-held="setPrinterStatus(printer, 'paused')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                  Pause
                </HoldButton>

                <HoldButton :disabled="printer.queue?.[0]?.extruded" :color="'warning'"
                  @button-held="setPrinterStatus(printer, 'colorchange')"
                  v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                  Color&nbsp;Change
                </HoldButton>

                <HoldButton :color="'secondary'" @button-held="setPrinterStatus(printer, 'printing')"
                  v-if="printer.status == 'paused'">
                  Unpause
                </HoldButton>

                <div v-if="printer.status == 'colorchange'" class="mt-2">
                  See LCD screen
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
                  <div type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#issueModal"
                    @click=setJob(printer.queue?.[0])>
                    Fail
                  </div>
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
                      <div class="dropdown-item" v-for="otherPrinter in printers.filter(p => p.id !== printer.id)"
                        :key="otherPrinter.id" @click="releasePrinter(printer.queue?.[0], 2, otherPrinter.id!)">
                        {{ otherPrinter.name }}
                      </div>
                    </div>
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
              <div v-else-if="printer.status == 'error'" class="alert alert-danger" role="alert">{{ printer?.error }}
              </div>

            </td>

            <td style="width: 1%; white-space: nowrap">
              <div class="dropdown">
                <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                  <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                    style="background: none; border: none;">
                    <i class="fas fa-ellipsis"></i>
                  </button>
                  <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                    <li>
                      <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                        data-bs-target="#infoModal" v-if="printer.queue && printer.queue.length > 0"
                        v-bind:job="printer.queue[0]"
                        @click="printer.name && openModal(printer.queue[0], printer.name, 0, printer)">
                        <i class="fas fa-info"></i>
                        <span class="ms-2">Info</span>
                      </a>
                    </li>
                    <!-- <li>
                      <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                        data-bs-target="#gcodeLiveViewModal" v-if="printer.queue && printer.queue.length > 0"
                        v-bind:job="printer.queue[0]"
                        @click="printer.name && openModal(printer.queue[0], printer.name, 1, printer)">
                        <i class="fa-solid fa-magnifying-glass"></i>
                        <span class="ms-2">GCode Live View</span>
                      </a>
                    </li> -->
                    <li>
                      <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                        data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                        v-bind:job="printer.queue[0]"
                        @click="printer.name && openModal(printer.queue[0], printer.name, 2, printer)">
                        <i class="fa-solid fa-image"></i>
                        <span class="ms-2">GCode Image</span>
                      </a>
                    </li>
                  </ul>
                </div>
              </div>
            </td>

            <td class="text-center handle" :class="{ 'not-draggable': printers.length <= 1 }">
              <i class="fas fa-grip-vertical" :class="{ 'icon-disabled': printers.length <= 1 }"></i>
            </td>
          </tr>
        </template>
      </draggable>
    </table>
    <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
        here</RouterLink>, or restart the server.
    </div>
  </div>
</template>

<style scoped>
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

table {
  table-layout: fixed;
  width: 100%;
  border-collapse: collapse;
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
</style>