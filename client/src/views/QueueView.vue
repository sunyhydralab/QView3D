<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRetrievePrintersInfo, type Device } from '../model/ports'
const { retrieveInfo } = useRetrievePrintersInfo()

type Printer = Device & { isExpanded?: boolean }
const printers = ref<Array<Printer>>([]) // Get list of open printer threads 

const toggleAccordion = (id: string) => {
  const printer = printers.value.find(p => p.id === Number(id))
  if (printer) {
    printer.isExpanded = !printer.isExpanded
  }
}

const rerunJob = (job: any) => {
  // TODO: Implement rerun job functionality
  console.log('Rerunning job:', job)
}

onMounted(async () => {
  try {
    printers.value = (await retrieveInfo()).map((printer: Device) => ({ ...printer, isExpanded: true }))
  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})
</script>

<template>
  <div class="container">
    <b>Queue View</b>
    <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">here</RouterLink>, or restart the server.</div>
    <div v-else class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item" v-for="(printer, index) in printers" :key="printer.id">
        <h2 class="accordion-header" id="panelsStayOpen-headingOne">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
            data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true" aria-controls="panelsStayOpen-collapseOne">
            {{ printer.name }}
          </button>
        </h2>
        <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show"
          aria-labelledby="panelsStayOpen-headingOne" data-bs-parent="#accordionPanelsStayOpenExample">
          <div class="accordion-body" v-for="job in printer.queue" :key="job.name">
            <table>
              <thead>
                <tr>
                  <th>Job Title</th>
                  <th>File</th>
                  <th>Date Added</th>
                  <th>Final Status</th>
                  <th>Rerun Job</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ job.name }}</td>
                  <td>{{ job.file_name }}</td>
                  <td>{{ job.date }}</td>
                  <td>{{ job.status }}</td>
                  <td><button type="button" class="btn btn-secondary" @click="rerunJob(job)">Rerun</button></td>
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
</style>
