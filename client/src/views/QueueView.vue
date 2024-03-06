<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, bumpJobs, type Job } from '../model/jobs';
import { useRoute } from 'vue-router'
import { nextTick } from 'vue';

const { retrieveInfo } = useRetrievePrintersInfo()
const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()
const { bumpjob } = bumpJobs()

const modalJob = ref<Job>();
const modalPrinter = ref<Printer>();
const selectedJobs = ref<Array<Job>>([]);
const selectedJobsMap = ref<Record<string, Job[]>>({});
// Map to track the state of "Select All" checkbox for each printer
const selectAllCheckboxMap = ref<Record<string, boolean>>({});

type Printer = Device & { isExpanded?: boolean }
const printers = ref<Array<Printer>>([]) // Get list of open printer threads 

let intervalId: number | undefined;
let selectAllCheckbox = ref(false);

onMounted(async () => {
  try {
    const route = useRoute()
    const printerName = route.params.printerName
    const updatePrinters = async () => {
      const printerInfo = await retrieveInfo()
      printers.value = []
      for (const printer of printerInfo) {
        printers.value.push({
          ...printer,
          isExpanded: printer.name === printerName
        })
      }
    }
    // Fetch the printer status immediately on mount
    await updatePrinters()
    // Then fetch it every 3 seconds
    intervalId = window.setInterval(updatePrinters, 3000)
  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})

onUnmounted(() => {
  // Clear the interval when the component is unmounted to prevent memory leaks
  if (intervalId) {
    clearInterval(intervalId)
  }
})

const handleRerun = async (job: Job, printer: Printer) => {
  await rerunJob(job, printer)
  // Re-fetch the printer's queue from the backend
  const printerInfo = await retrieveInfo()
  const foundPrinter = printerInfo.find((p: any) => p.id === printer.id)
  if (foundPrinter) {
    const printerIndex = printers.value.findIndex(p => p.id === printer.id)
    if (printerIndex !== -1) {
      printers.value[printerIndex].queue = foundPrinter.queue
    }
  }
};

const deleteSelectedJobs = async () => {
  // Loop through the selected jobs and remove them from the printer's queue
  for (const selectedJob of selectedJobs.value) {
    const foundPrinter = printers.value.find((printer) => printer.id === selectedJob.printerid);
    if (foundPrinter) {
      const jobIndex = foundPrinter.queue?.findIndex((job) => job.id === selectedJob.id);
      if (jobIndex !== undefined && jobIndex !== -1) {
        foundPrinter.queue?.splice(jobIndex, 1); // Remove the job from the printer's queue
        console.log("Heyyyyyyyyy")
      }
    }
    await removeJob(selectedJob);
  }

  // Clear the selected jobs array
  selectedJobs.value = [];
  selectAllCheckbox.value = false;
};

const SelectAllJobs = (printer: Printer | undefined) => {
  if (printer !== undefined && printer.queue !== undefined) {
    // Toggle the "Select All" checkbox state for the current printer
    selectAllCheckboxMap.value[printer.id!] = !selectAllCheckboxMap.value[printer.id!];

    // Update the selected jobs for the current printer based on the "Select All" checkbox state
    selectedJobsMap.value[printer.id!] = selectAllCheckboxMap.value[printer.id!] ? [...printer.queue] : [];

    // Update the selectedJobs array by combining selected jobs from all printers
    selectedJobs.value = Object.values(selectedJobsMap.value).flat();
  }
};



function capitalizeFirstLetter(string: string | undefined) {
  return string ? string.charAt(0).toUpperCase() + string.slice(1) : '';
}

function statusColor(status: string | undefined) {
  switch (status) {
    case 'ready':
      return 'green';
    case 'error':
      return 'red';
    case 'offline':
      return 'darkred';
    case 'printing':
      return 'blue';
    case 'complete':
      return 'darkgreen';
    default:
      return 'black';
  }
}

const bump = async (job: Job, printer: Printer, direction: string) => {
  switch (direction) {
    case 'up':
      await bumpjob(job, printer, 1)
      break;
    case 'down':
      await bumpjob(job, printer, 2)
      break;
    case 'top':
      await bumpjob(job, printer, 3)
      break;
    case 'bottom':
      await bumpjob(job, printer, 4)
      break;
  }


  // Re-fetch the printer's queue from the backend
  const printerInfo = await retrieveInfo()
  const foundPrinter = printerInfo.find((p: any) => p.id === printer.id)
  if (foundPrinter) {
    const printerIndex = printers.value.findIndex(p => p.id === printer.id)
    if (printerIndex !== -1) {
      printers.value[printerIndex].queue = foundPrinter.queue
    }
  }
}

const isLastJob = (job: Job, printer: Printer) => {
  return printer.queue ? printer.queue.indexOf(job) === printer.queue.length - 1 : false;
}
const isFirstJobPrinting = (job: Job, printer: Printer) => {
  if (!printer.queue) return false;
  return printer.queue[0] && printer.queue[0].status === 'printing';
}
const canBumpUp = (job: Job, printer: Printer) => {
  if (!printer.queue) return false;
  const index = printer.queue.indexOf(job);
  return index !== 0 && (index !== 1 || !isFirstJobPrinting(job, printer));
}
</script>

<template>
  <div class="container">

    <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true" data-bs-backdrop="static">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Removing {{ selectedJobs.length }} job(s) from queue!</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to remove these job(s) from queue? Job will be saved to history with a final status of <i>cancelled</i>.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-danger" data-bs-dismiss="modal" @click="deleteSelectedJobs">Remove</button>

          </div>
        </div>
      </div>
    </div>

    <b>Queue View</b>
    <button class="btn btn-danger w-100" data-bs-toggle="modal" 
    data-bs-target="#exampleModal" :disabled="selectedJobs.length === 0" >
      Remove from queue
    </button>

    <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">here
      </RouterLink>, or restart the server.</div>

    <div v-else class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item" v-for="(printer, index) in printers" :key="printer.id">
        <h2 class="accordion-header" :id="'panelsStayOpen-heading' + index">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
            :data-bs-target="'#panelsStayOpen-collapse' + index" :aria-expanded="printer.isExpanded"
            :aria-controls="'panelsStayOpen-collapse' + index">
            <b>{{ printer.name }}:&nbsp;
              <span class="status-text" :style="{ color: statusColor(printer.status) }">{{
                capitalizeFirstLetter(printer.status) }}</span>
            </b>
          </button>
        </h2>
        <div :id="'panelsStayOpen-collapse' + index" class="accordion-collapse collapse"
          :class="{ show: printer.isExpanded }" :aria-labelledby="'panelsStayOpen-heading' + index"
          data-bs-parent="#accordionPanelsStayOpenExample">
          <div class="accordion-body">
            <table>
              <thead>
                <tr>
                  <th class="col-1">Job ID</th>
                  <th class="col-checkbox">
                    <input type="checkbox" @change="() => SelectAllJobs(printer)" />
                  </th>
                  <th class="col-2">Rerun Job</th>
                  <th class="col-1">Position</th>
                  <th class="col-1">Bump</th>
                  <th>Job Title</th>
                  <th>File</th>
                  <th>Date Added</th>
                  <th class="col-1">Job Status</th>
                </tr>
              </thead>
              <transition-group name="list" tag="tbody">
                <tr v-for="job in printer.queue" :key="job.id">
                  <td>{{ job.id }}</td>
                  <td class="text-center">
                    <input type="checkbox" v-model="selectedJobs" :value="job" />
                  </td>

                  <td class="text-center">
                    <div class="btn-group w-100">
                      <button type="button" class="btn btn-primary" @click="handleRerun(job, printer)">Rerun
                        Job</button>
                      <button type="button" class="btn btn-primary dropdown-toggle dropdown-toggle-split"
                        data-bs-toggle="dropdown" aria-expanded="false">
                        <span class="visually-hidden">Toggle Dropdown</span>
                      </button>
                      <div class="dropdown-menu">
                        <button class="dropdown-item" v-for="otherPrinter in printers.filter(p => p.id !== printer.id)"
                          :key="otherPrinter.id" @click="handleRerun(job, otherPrinter)">{{ otherPrinter.name
                          }}</button>
                      </div>
                    </div>
                  </td>

                  <td class="text-center">
                    <b>
                      {{ printer.queue ? printer.queue.findIndex(j => j === job) + 1 : '' }}
                    </b>
                  </td>

                  <td class="text-center">
                    <div class="dropdown w-100">
                      <button class="btn dropdown-toggle w-100"
                        :class="{ 'btn-danger': printer.queue && job.status === 'printing', 'btn-secondary': !printer.queue || (printer.queue && job.status !== 'printing') }"
                        type="button" data-bs-toggle="dropdown"
                        :disabled="printer.queue && job.status === 'printing'"></button>
                      <ul class="dropdown-menu">
                        <li class="dropdown-item" v-if="canBumpUp(job, printer)" @click="bump(job, printer, 'up')">Bump Up
                        </li>
                        <li class="dropdown-item" v-if="canBumpUp(job, printer)" @click="bump(job, printer, 'top')">Send
                          to Top</li>
                        <li class="dropdown-item" v-if="!isLastJob(job, printer)" @click="bump(job, printer, 'down')">Bump
                          Down</li>
                        <li class="dropdown-item" v-if="!isLastJob(job, printer)" @click="bump(job, printer, 'bottom')">
                          Send to Bottom</li>
                      </ul>
                    </div>
                  </td>
                  <td><b>{{ job.name }}</b></td>
                  <td>{{ job.file_name_original }}</td>
                  <td>{{ job.date }}</td>
                  <td>{{ job.status }}</td>
                </tr>
              </transition-group>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-move {
  transition: transform 1s;
}

table {
  width: 100%;
  border-collapse: collapse;
  border: 0px;
}

th,
td {
  border: 1px solid #dddddd;
  text-align: left;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

.accordion-body {
  padding: 0;
}

/* HARDCODED */
.accordion-item {
  width: 1296px;
}

.accordion-button:not(.collapsed) {
  background-color: #f2f2f2;
}

.accordion-button:focus {
  box-shadow: none;
}

.accordion-button {
  color: black;
  display: flex;
}

.accordion-button:not(.collapsed)::after {
  background-image: var(--bs-accordion-btn-icon);
}

.dropbtn {
  background-color: #4CAF50;
  color: white;
  padding: 16px;
  font-size: 16px;
  border: none;
  cursor: pointer;
}

/* The container <div> - needed to position the dropdown content */
.dropdown {
  position: relative;
  display: inline-block;
}

/* Dropdown Content (Hidden by Default) */
.dropdown-content {
  display: none;
  position: absolute;
  background-color: #f9f9f9;
  min-width: 160px;
  box-shadow: 0px 8px 16px 0px rgba(0, 0, 0, 0.2);
  z-index: 1;
}

/* Links inside the dropdown */
.dropdown-content a {
  color: black;
  padding: 12px 16px;
  text-decoration: none;
  display: block;
}

/* Change color of dropdown links on hover */
.dropdown-content a:hover {
  background-color: #f1f1f1
}

/* Show the dropdown menu on hover */
.dropdown:hover .dropdown-content {
  display: block;
}

/* Change the background color of the dropdown button when the dropdown content is shown */
.dropdown:hover .dropbtn {
  background-color: #3e8e41;
}

.printerrerun {
  cursor: pointer;
  padding: 12px 16px;
}

.modal-backdrop {
  display: none;
}
</style>
