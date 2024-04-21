<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { printers, type Device } from '@/model/ports';
import draggable from 'vuedraggable'
import PrinterRow from '@/components/PrinterRow.vue'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import { useAssignIssue, useGetIssues, type Issue } from '@/model/issues';
import { jobTime, useAssignComment, useGetFile, useReleaseJob, type Job } from '@/model/jobs';

const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { releaseJob } = useReleaseJob()
const { issues } = useGetIssues()
const { getFile } = useGetFile()

const selectedIssue = ref<Issue>()
const selectedJob = ref<Job>()
let jobComments = ref('')

let currentJob = ref<Job>();
let currentPrinter = ref<Device>();

let issuelist = ref<Array<Issue>>([])

let isGcodeImageVisible = ref(false)
let isGcodeLiveViewVisible = ref(false)

let expandedState: (string | undefined)[] = [];

onMounted(async () => {
  const retrieveissues = await issues()
  issuelist.value = retrieveissues
})

function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60)
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

  const hoursStr = hours < 10 ? '0' + hours : hours
  const minutesStr = minutes < 10 ? '0' + minutes : minutes
  const secondsStr = seconds < 10 ? '0' + seconds : seconds

  if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN')) return '<i>idle</i>'
  return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds)
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })


  if (isNaN(date.getTime()) || timeString === "07:00 PM") {
    return '<i>idle</i>'
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
  await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid)

  if (selectedIssue.value !== undefined) {
    await assign(selectedIssue.value.id, selectedJob.value.id)
  }
  await assignComment(selectedJob.value, jobComments.value)
  selectedJob.value.comment = jobComments.value
  selectedIssue.value = undefined
  selectedJob.value = undefined
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

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {
  await releaseJob(jobToFind, key, printerIdToPrintTo)
}

const setJob = async (job: Job) => {
  jobComments.value = job.comment || '';
  selectedJob.value = job;
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
          <button type="button" class="btn btn-success" data-bs-dismiss="modal" @click="doAssignIssue">Save
            Changes</button>
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
          <h5 class="modal-title" id="gcodeModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name
            }}</h5>
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
        dragClass="hidden-ghost" v-if="printers.length > 0" @start="collapseAll" @end="restoreExpandedState">
        <template #item="{ element: printer }">
          <div v-if="printer.isInfoExpanded" class="expanded-info">
            <tr :id="printer.id">
              <PrinterRow :printer="printer" :openModal="openModal" :setJob="setJob" />
            </tr>
            <tr style="background-color: #cdcdcd;">
              <td class="borderless-bottom">
                <b>Filament:</b>
              </td>
              <td class="borderless-bottom">
                <b>Layer:</b>
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
              <td class="borderless-bottom border-extended">
                <b>ETA:</b>
              </td>
            </tr>
            <tr style="background-color: #cdcdcd;">
              <td class="borderless-top">
                <span></span>
              </td>
              <td class="borderless-top">
                <span></span>
              </td>
              <td class="borderless-top">
                <span v-html="printer?.extruder_temp ? printer.extruder_temp + '&deg;C' : '<i>idle</i>'"></span>
              </td>
              <td class="borderless-top">
                <span v-html="printer?.bed_temp ? printer.bed_temp + '&deg;C' : '<i>idle</i>'"></span>
              </td>
              <td class="borderless-top">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.elapsed_time!)"></span>
              </td>
              <td class="borderless-top">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.remaining_time!)"></span>
              </td>
              <td class="borderless-top">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.total_time!)"></span>
              </td>
              <td class="borderless-top border-extended">
                <span
                  v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatETA(printer.queue[0]?.job_client?.eta!)"></span>
              </td>
            </tr>
          </div>
          <tr v-else :id="printer.id">
            <PrinterRow :printer="printer" :openModal="openModal" :setJob="setJob" />
          </tr>
        </template>
      </draggable>
    </table>
    <div v-if="printers.length === 0" style="margin-top: 1rem;">
      No printers available. Either register a printer <RouterLink to="/registration">here</RouterLink>, or restart the
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

.border-extended {
  position: relative;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.hidden-ghost {
  opacity: 0;
}

.border-extended::after {
  content: "";
  position: absolute;
  right: 0px;
  top: -0.5px;
  bottom: 0;
  width: 1px;
  background: #929292;
  height: calc(100% + 1.5px);
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
</style>