<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useRerunJob, useRemoveJob, type Job } from '@/model/jobs';
const { retrieveInfo } = useRetrievePrintersInfo()
const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()

type Printer = Device & { isExpanded?: boolean }
const printers = ref<Array<Printer>>([]) // Get list of open printer threads 

onMounted(async () => {
  try {
    printers.value = (await retrieveInfo()).map((printer: Device) => ({ ...printer, isExpanded: true }))
  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})

const toggleAccordion = (id: string) => {
  const printer = printers.value.find(p => p.id === Number(id))
  if (printer) {
    printer.isExpanded = !printer.isExpanded
  }
}

const handleRerun = async (job: Job, printer: Printer) => {
  await rerunJob(job, printer)
  console.log('Rerunning job:', job, 'on printer:', printer);
};

async function handleCancel(jobToFind: Job, printerToFind: Device) {
  // remove from in-memory array 
  const foundPrinter = printers.value.find(printer => printer === printerToFind); // Find the printer by direct object comparison
  if (!foundPrinter) return; // Return if printer not found
  const jobIndex = foundPrinter.queue?.findIndex(job => job === jobToFind); // Find the index of the job in the printer's queue
  if (jobIndex === undefined || jobIndex === -1) return; // Return if job not found
  foundPrinter.queue?.splice(jobIndex, 1); // Remove the job from the printer's queue

  // remove from queue 
  await removeJob(jobToFind)
}
</script>

<template>
  <div class="container">
    <b>Queue View</b>

    <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">here
      </RouterLink>, or restart the server.</div>

    <div v-else class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item" v-for="(printer, index) in printers" :key="printer.id">
        <h2 class="accordion-header" id="panelsStayOpen-headingOne">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
            data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
            <b>{{ printer.name }} </b>
          </button>
        </h2>
        <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show"
          aria-labelledby="panelsStayOpen-headingOne" data-bs-parent="#accordionPanelsStayOpenExample">
          <div class="accordion-body">
            <div>
              Printer Status: <b>{{ printer.status }} </b>
            </div>
            <table>
              <thead>
                <tr>
                  <th>Cancel</th>
                  <th>Job Title</th>
                  <th>File</th>
                  <th>Date Added</th>
                  <th>Status</th>
                  <th>Rerun Job</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="job in printer.queue" :key="job.name">
                  <td>
                    <button @click="handleCancel(job, printer)">X</button>
                  </td>
                  <td><b>{{ job.name }}</b></td>
                  <td>{{ job.file_name }}</td>
                  <td>{{ job.date }}</td>
                  <td>{{ job.status }}</td>
                  <td>
                    <div class="dropdown">
                      <button class="dropbtn">Rerun Job</button>
                      <div class="dropdown-content">
                        <div v-for="printer in printers" :key="printer.id">
                          <div class="printerrerun" @click="handleRerun(job, printer)">{{ printer.name }}</div>
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>

              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
</style>
