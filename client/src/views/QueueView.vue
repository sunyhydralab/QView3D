<script setup lang="ts">
import { onUnmounted, ref, computed } from 'vue'
import { printers, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, type Job, useMoveJob, useGetFile } from '../model/jobs';
import draggable from 'vuedraggable'
import { toast } from '@/model/toast';
import { useRouter } from 'vue-router'
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'

const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()
const { moveJob } = useMoveJob()
const { getFile } = useGetFile()
const router = useRouter()

const selectedJobs = ref<Array<Job>>([]);
const selectAllCheckboxMap = ref<Record<string, boolean>>({});

let currentJob = ref<Job | null>(null);
let isGcodeImageVisible = ref(false);
let selectAllCheckbox = ref(false);

onUnmounted(() => {
  for (const printer of printers.value) {
    printer.isExpanded = false;
  }
});

const handleRerun = async (job: Job, printer: Device) => {
  await rerunJob(job, printer)
};

const handleRerunToSubmit = async (job: Job, printer: Device) => {
  await router.push({
        name: 'SubmitJobVue', // the name of the route to SubmitJob.vue
        params: { job: JSON.stringify(job), printer: JSON.stringify(printer) } // the job and printer to fill in the form
    });
};

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
      // but only if the job's status is 'inqueue'
      selectedJobs.value = [
        ...selectedJobs.value,
        ...printer.queue.filter(job => job.status === 'inqueue')
      ];
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
  const printerId = Number(evt.item.dataset.printerId);
  const arr = Array.from(evt.to.children).map((child: any) => Number(child.dataset.jobId));
  await moveJob(printerId, arr)
};

const isInqueue = (evt: any) => {
  return evt.relatedContext.element.status === 'inqueue';
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
            <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob!" />
          </div>
        </div>
      </div>
    </div>
  </div>

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
          @show.bs.collapse="printer.isExpanded = !printer.isExpanded">
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
                  <th>Actions</th>
                  <th style="width: 0">Move</th>
                </tr>
              </thead>
              <draggable v-model="printer.queue" tag="tbody" :animation="300" itemKey="job.id" handle=".handle"
                dragClass="hidden-ghost" :onEnd="handleDragEnd" v-if="printer.queue && printer.queue.length"
                :move="isInqueue">
                <template #item="{ element: job }">
                  <tr :id="job.id.toString()" :data-printer-id="printer.id" :data-job-id="job.id"
                    :data-job-status="job.status" :key="job.id" :class="{ 'printing': job.status === 'printing' }">
                    <td>{{ job.id }}</td>
                    <td class="text-center">
                      <input type="checkbox" v-model="selectedJobs" :value="job" 
                        :disabled="job.status !== 'inqueue'"/>
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
                    <td style="width: ">
                      <div class="dropdown">
                        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                          <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                            style="background: none; border: none;">
                            <i class="fas fa-ellipsis"></i>
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
</template>

<style scoped>
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

.printerrerun {
  cursor: pointer;
  padding: 12px 16px;
}

.modal-backdrop {
  display: none;
}
</style>
