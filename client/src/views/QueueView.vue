<script setup lang="ts">
import { ref } from 'vue'
import { printers, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, type Job, useMoveJob } from '../model/jobs';
import draggable from 'vuedraggable'

const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()
const { moveJob } = useMoveJob()

const selectedJobs = ref<Array<Job>>([]);
const selectAllCheckboxMap = ref<Record<string, boolean>>({});

let selectAllCheckbox = ref(false);

const handleRerun = async (job: Job, printer: Device) => {
  await rerunJob(job, printer)
};

const deleteSelectedJobs = async () => {
  // Loop through the selected jobs and remove them from the printer's queue
  for (const selectedJob of selectedJobs.value) {
    const foundPrinter = printers.value.find((printer) => printer.id === selectedJob.printerid);
    if (foundPrinter) {
      const jobIndex = foundPrinter.queue?.findIndex((job) => job.id === selectedJob.id);
      if (jobIndex !== undefined && jobIndex !== -1) {
        foundPrinter.queue?.splice(jobIndex, 1); // Remove the job from the printer's queue
      }
    }
    await removeJob(selectedJob);
  }
  // Clear the selected jobs array
  selectedJobs.value = [];
  selectAllCheckbox.value = false;
};

const selectAllJobs = (printer: Device) => {
  if (printer !== undefined && printer.queue !== undefined) {
    // Toggle the "Select All" checkbox state for the current printer
    selectAllCheckboxMap.value[printer.id!] = !selectAllCheckboxMap.value[printer.id!];

    if (selectAllCheckboxMap.value[printer.id!]) {
      // If the "Select All" checkbox for the current printer is checked,
      // add all jobs from the current printer to the selectedJobs array
      selectedJobs.value = [...selectedJobs.value, ...printer.queue];
    } else {
      // Otherwise, remove all jobs from the current printer from the selectedJobs array
      selectedJobs.value = selectedJobs.value.filter(job => job.printerid !== printer.id);
    }
  }
}

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

const handleDragEnd = async (evt: any) => {
  if (evt.newIndex != 1) {
    const printerId = Number(evt.item.dataset.printerId);
    const arr = Array.from(evt.to.children).map((child: any) => Number(child.dataset.jobId));
    await moveJob(printerId, arr)
  }
};

</script>

<template>
  <div class="container">

    <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true"
      data-bs-backdrop="static">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="exampleModalLabel">Removing {{ selectedJobs.length }} job(s) from queue!</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>Are you sure you want to remove these job(s) from queue? Job will be saved to history with a final status
              of <i>cancelled</i>.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
            <button type="button" class="btn btn-danger" data-bs-dismiss="modal"
              @click="deleteSelectedJobs">Remove</button>

          </div>
        </div>
      </div>
    </div>

    <b>Queue View</b>
    <button class="btn btn-danger w-100" data-bs-toggle="modal" data-bs-target="#exampleModal"
      :disabled="selectedJobs.length === 0">
      Remove from queue
    </button>

    <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
        here
      </RouterLink>, or restart the server.</div>

    <div v-else class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item" v-for="(printer, index) in printers" :key="printer.id">
        <h2 class="accordion-header" :id="'panelsStayOpen-heading' + index">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
            :data-bs-target="'#panelsStayOpen-collapse' + index" :aria-expanded="printer.isExpanded"
            :aria-controls="'panelsStayOpen-collapse' + index" :class="{ 'collapsed': !printer.isExpanded }">
            <b>{{ printer.name }}:&nbsp;
              <span class="status-text" :style="{ color: statusColor(printer.status) }">{{
              capitalizeFirstLetter(printer.status) }}</span>
            </b>
          </button>
        </h2>
        <div :id="'panelsStayOpen-collapse' + index" class="accordion-collapse collapse"
          :class="{ show: printer.isExpanded }" :aria-labelledby="'panelsStayOpen-heading' + index"
          data-bs-parent="#accordionPanelsStayOpenExample" @show.bs.collapse="printer.isExpanded = !printer.isExpanded">
          <div class="accordion-body">
            <table>
              <thead>
                <tr>
                  <th class="col-1">Job ID</th>
                  <th class="col-checkbox">
                    <div class="checkbox-container">
                      <input type="checkbox" @change="() => selectAllJobs(printer)"
                        :disabled="printer.queue!.length === 0" />
                    </div>
                  </th>
                  <th class="col-2">Rerun Job</th>
                  <th class="col-1">Position</th>
                  <th>Job Title</th>
                  <th>File</th>
                  <th>Date Added</th>
                  <th class="col-1">Job Status</th>
                  <th style="width: 0">Move</th>
                </tr>
              </thead>
              <draggable v-model="printer.queue" tag="tbody" :animation="300" itemKey="job.id" handle=".handle"
                dragClass="hidden-ghost" :onEnd="handleDragEnd" v-if="printer.queue && printer.queue.length">
                <template #item="{ element: job }">
                  <tr :id="job.id.toString()" :data-printer-id="printer.id" :data-job-id="job.id"
                    :data-job-status="job.status" :key="job.id" :class="{ 'printing': job.status === 'printing' }">
                    <td>{{ job.id }}</td>
                    <td class="text-center">
                      <input type="checkbox" v-model="selectedJobs" :value="job" />
                    </td>

                    <td class="text-center">
                      <div class="btn-group w-100">
                        <div class="btn btn-primary" @click="handleRerun(job, printer)">Rerun
                          Job</div>
                        <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                          aria-expanded="false">
                        </div>
                        <div class="dropdown-menu">
                          <div class="dropdown-item" v-for="otherPrinter in printers.filter(p => p.id !== printer.id)"
                            :key="otherPrinter.id" @click="handleRerun(job, otherPrinter)">{{ otherPrinter.name
                            }}</div>
                        </div>
                      </div>
                    </td>

                    <td class="text-center">
                      <b>
                        {{ printer.queue ? printer.queue.findIndex(j => j === job) + 1 : '' }}
                      </b>
                    </td>
                    <td><b>{{ job.name }}</b></td>
                    <td>{{ job.file_name_original }}</td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <td class="text-center handle" :class="{ 'not-draggable': job.status !== 'inqueue' }">
                      <i class="fas fa-grip-vertical" :class="{ 'icon-disabled': job.status !== 'inqueue' }"></i>
                    </td>
                  </tr>
                </template>
              </draggable>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-draggable {
  user-select: none;
  pointer-events: none;
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
