<script setup lang="ts">
import { useSetStatus, type Device, printers } from '@/model/ports';
import { type Job, useReleaseJob } from '@/model/jobs';
import { useRouter } from 'vue-router';
import { ref } from 'vue';
import draggable from 'vuedraggable'

const { setStatus } = useSetStatus();
const { releaseJob } = useReleaseJob()

const router = useRouter();
let currentJob = ref<Job>();
let currentPrinter = ref<Device>();

let isGcodeImageVisible = ref(false)
let isGcodeLiveViewVisible = ref(false)

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

const openModal = (job: Job, printerName: string, num: number, printer: Device) => {
  currentJob.value = job
  currentJob.value.printer = printerName
  currentPrinter.value = printer
  if (num == 1) {
    // isGcodeLiveViewVisible.value = true
  } else if (num == 2) {
    // isGcodeImageVisible.value = true
  }
}

function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60)
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

  const hoursStr = hours < 10 ? '0' + hours : hours
  const minutesStr = minutes < 10 ? '0' + minutes : minutes
  const secondsStr = seconds < 10 ? '0' + seconds : seconds

  if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN') || (hoursStr + ':' + minutesStr + ':' + secondsStr === '00:00:00')) return 'Waiting to start heating...'
  return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds)
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })

  if (isNaN(date.getTime()) || timeString === "07:00 PM") {
    return 'Waiting to start heating...'
  }

  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}
</script>

<template>
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
                    <div class="col-12">{{ formatTime(currentJob?.elapsed_time!) }}</div>
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
                    <div class="col-12">{{ formatTime(currentJob?.remaining_time!) }}</div>
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
                      <div v-if="currentJob?.extra_time && currentJob.extra_time > 0">
                        {{ formatTime(currentJob.total_time!) + ' + ' + formatTime(currentJob.extra_time!) }}
                      </div>
                      <div v-else>
                        {{ formatTime(currentJob?.total_time!) }}
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
                    <div class="col-12">{{ (formatETA(currentJob?.eta!) ?? "00:00 AM") }}</div>
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
            <!-- <GCode3DLiveViewer v-if="isGcodeLiveViewVisible" :job="currentJob" /> -->
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
            <!-- <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob" /> -->
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
    <b>Home</b>
    <table>
      <tr>
        <th>Job ID</th>
        <th>Printer name</th>
        <th>Printer Status</th>
        <th>Job Name</th>
        <th>File</th>
        <th>Progress</th>
        <th>Actions</th>
        <th style="width: 0px">Move</th>
      </tr>
      <tr v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
          here</RouterLink>, or restart the server.</tr>

      <draggable v-model="printers" tag="tbody" :animation="300" item-key="printer.id" handle=".handle"
        dragClass="hidden-ghost" v-if="printers.length > 0">
        <template #item="{ element: printer }">
          <tr :id="printer.id">
            <td v-if="printer.status &&
            (printer.status === 'printing' ||
              printer.status === 'complete' ||
              printer.status == 'paused') &&
            printer.queue &&
            printer.queue.length > 0 &&
            printer.queue?.[0].status != 'inqueue'
            ">
              {{ printer.queue?.[0].id }}
            </td>
            <td v-else><i>idle</i></td>
            <td>
              <button type="button" class="btn btn-link" @click="sendToQueueView(printer)">
                {{ printer.name }}
              </button>
            </td>
            <td>
              <div class="d-flex align-items-center">
                <p class="mb-0 me-2">{{ printer.status }}</p>
                <div class="dropdown">
                  <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton"
                    data-bs-toggle="dropdown" aria-expanded="false">
                    Change Status
                  </button>
                  <ul class="dropdown-menu" aria-labelledby="dropdownMenuButton">
                    <li v-if="printer.status == 'configuring' ||
            printer.status == 'ready' ||
            printer.status == 'error' ||
            printer.status == 'complete'
            ">
                      <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'offline')">Turn Offline</a>
                    </li>
                    <li v-if="printer.status == 'configuring' ||
            printer.status == 'offline' ||
            printer.status == 'error'
            ">
                      <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'ready')">Set to Ready</a>
                    </li>
                    <li v-if="printer.status == 'printing'">
                      <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'complete')">Stop Print</a>
                    </li>
                    <li v-if="printer.status == 'printing'">
                      <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'paused')">Pause Print</a>
                    </li>
                    <li v-if="printer.status == 'paused'">
                      <a class="dropdown-item" href="#" @click="setPrinterStatus(printer, 'printing')">Unpause Print</a>
                    </li>
                  </ul>
                </div>
              </div>
            </td>

            <td v-if="printer.status == 'printing' ||
            printer.status == 'complete' ||
            printer.status == 'paused' ||
            (printer.status == 'offline' &&
              (printer.queue?.[0]?.status == 'complete' ||
                printer.queue?.[0]?.status == 'cancelled'))
            ">
              {{ printer.queue?.[0]?.name }}
            </td>
            <td v-else></td>
            <td v-if="(printer.queue &&
            printer.queue.length > 0 &&
            (printer.status == 'printing' ||
              printer.status == 'complete' ||
              printer.status == 'paused')) ||
            (printer.status == 'offline' &&
              (printer.queue?.[0]?.status == 'complete' ||
                printer.queue?.[0]?.status == 'cancelled'))
            ">
              {{ printer.queue?.[0]?.file_name_original }}
            </td>
            <td v-else></td>

            <!-- <div class="spinner-border" role="status">
              <span class="sr-only">Loading...</span>
            </div> -->

            <td style="width: 250px">
              <div v-if="(printer.status === 'printing' || printer.status == 'paused') &&
            printer.queue &&
            printer.queue.length > 0
            ">
                <!-- <div v-for="job in printer.queue" :key="job.id"> -->
                <!-- Display the elapsed time -->
                <div class="progress" style="position: relative">
                  <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                    :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"
                    :aria-valuenow="printer.queue?.[0].progress" aria-valuemin="0" aria-valuemax="100"></div>
                  <!-- job progress set to 2 decimal places -->
                  <p style="position: absolute; width: 100%; text-align: center; color: black">
                    {{
            printer.queue?.[0].progress
              ? `${printer.queue?.[0].progress.toFixed(2)}%`
              : '0.00%'
          }}
                  </p>
                </div>
                <!-- </div> -->
              </div>

              <div v-else-if="printer.queue?.[0] &&
            (printer.queue?.[0].status == 'complete' ||
              printer.queue?.[0].status == 'cancelled')
            ">
                <div class="buttons">
                  <div type="button" class="btn btn-danger" @click="releasePrinter(printer.queue?.[0], 3, printer.id)">
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
              <div v-else-if="printer.queue?.[0] &&
            printer.queue?.[0].status == 'printing' &&
            printer.status == 'complete'
            ">
                <button class="btn btn-primary" type="button" disabled>
                  <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                  <span class="sr-only">Finishing print...</span>
                </button>
              </div>
              <div v-else-if="printer.status == 'error'" class="alert alert-danger" role="alert">
                {{ printer?.error }}
              </div>
            </td>

            <td style="width: 1%; white-space: nowrap">
              <!-- to display buttons when job is in queue and not printing -->
              <!-- <div v-if="printer.status == 'printing'"> -->
              <div style="display: inline-flex">
                <button type="button" class="btn btn-primary btn-circle me-2" data-bs-toggle="modal"
                  data-bs-target="#infoModal" v-if="printer.queue && printer.queue.length > 0"
                  v-bind:job="printer.queue[0]" @click="printer.name && openModal(printer.queue[0], printer.name, 0, printer)">
                  <i class="fas fa-info"></i>
                </button>
                <button type="button" class="btn btn-success btn-circle me-2" data-bs-toggle="modal"
                  data-bs-target="#gcodeLiveViewModal" v-if="printer.queue && printer.queue.length > 0"
                  v-bind:job="printer.queue[0]" @click="printer.name && openModal(printer.queue[0], printer.name, 1, printer)">
                  <i class="fas fa-code"></i>
                </button>
                <button type="button" class="btn btn-info btn-circle" data-bs-toggle="modal"
                  data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                  v-bind:job="printer.queue[0]" @click="printer.name && openModal(printer.queue[0], printer.name, 2, printer)">
                  <i class="fa-regular fa-image"></i>
                </button>
              </div>
              <!-- </div> -->
            </td>
            <td class="text-center handle" :class="{ 'not-draggable': printers.length <= 1 }">
              <i class="fas fa-grip-vertical" :class="{ 'icon-disabled': printers.length <= 1 }"></i>
            </td>
          </tr>
        </template>
      </draggable>
    </table>
  </div>
</template>

<style scoped>
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
  visibility: hidden;
}

.buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.buttons>* {
  margin: 0 0.375rem;
}

.no-wrap {
  white-space: nowrap;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 2px solid #dddddd;
  text-align: left;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

p {
  margin: 0;
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