<script setup lang="ts">
import { useRetrievePrintersInfo, useSetStatus, setupStatusSocket, disconnectStatusSocket, type Device } from '@/model/ports';
import { type Job, useReleaseJob, useRemoveJob, setupProgressSocket, disconnectProgressSocket } from '@/model/jobs';
import { useRouter, useRoute } from 'vue-router';
import { onMounted, onUnmounted, ref } from 'vue';

const { retrieveInfo } = useRetrievePrintersInfo();
const { setStatus } = useSetStatus();
const { releaseJob } = useReleaseJob()
const { removeJob } = useRemoveJob()

const router = useRouter();

let printers = ref<Array<Device>>([]); // Array of all devices. Used to list registered printers on frontend. 

let intervalId: number | undefined;

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
    // Setup the satus socket
    setupStatusSocket(printers)
    // Setup the progress socket
    setupProgressSocket(printers.value)

    console.log("PRINTERS: ", printers.value)

  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})

onUnmounted(() => {
  // Clear the interval when the component is unmounted to prevent memory leaks
  if (intervalId) {
    clearInterval(intervalId)
  }

  // Disconnect the status socket
  disconnectStatusSocket()
  // Disconnect the progress socket
  disconnectProgressSocket()
})

const sendToQueueView = (name: string | undefined) => {
  if (name) {
    router.push({ name: 'QueueViewVue', params: { printerName: name } });
  }
}

// set the status of the printer
const setPrinterStatus = async (printer: Device, status: string) => {
  printer.status = status; // update the status in the frontend
  await setStatus(printer.id, status); // update the status in the backend
  if ((status == 'offline' && printer.queue?.[0]?.status == 'printing') || status == "complete") {
    if (printer.queue && printer.queue.length > 0) {
      printer.queue[0].status = "cancelled";
      await removeJob(printer.queue?.[0])
    }
  }

  setTimeout(() => {
    // Using setTimeout to ensure the value is reset after the change event is processed
    const selectElement = document.querySelector('select');
    if (selectElement) {
      (selectElement as HTMLSelectElement).value = '';
    }
  });
}

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerToFind: Device, printerIdToPrintTo: number | undefined, status: string) => {
  const foundPrinter = printers.value.find(printer => printer === printerToFind); // Find the printer by direct object comparison
  if (!foundPrinter) return; // Return if printer not found
  else {
    const jobIndex = foundPrinter.queue?.findIndex(job => job === jobToFind); // Find the index of the job in the printer's queue
    if (jobIndex === undefined || jobIndex === -1) return; // Return if job not found
    foundPrinter.queue?.shift(); // This will remove the first job from the queue
    foundPrinter.status = status; // Set the printer status to ready
    
    await releaseJob(jobToFind, key, printerIdToPrintTo)
  }
}

</script>

<template>
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
      </tr>
      <tr v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
          here</RouterLink>, or restart the server.</tr>

      <tr v-for="printer in printers" :key="printer.name">
        <td
          v-if="(printer.status && (printer.status === 'printing' || printer.status === 'complete')) && (printer.queue && printer.queue.length > 0 && printer.queue?.[0].status != 'inqueue')">
          {{ printer.queue?.[0].id }}</td>
        <td v-else><i>idle</i></td>
        <td><button type="button" class="btn btn-link" @click="sendToQueueView(printer.name)">{{ printer.name }}</button>
        </td>

        <td>
          <p>{{ printer.status }}</p>
          <select @change="setPrinterStatus(printer, ($event.target as HTMLSelectElement).value)">
            <option value="">Change Status</option> <!-- Default option -->
            <option value="offline">Turn Offline</option>
            <option value="ready">Set to Ready</option>
            <option v-if="printer.status == 'printing'" value="complete">Stop Print</option>
          </select>
        </td>

        <td v-if="(printer.queue && printer.queue.length > 0 && printer.queue?.[0]?.status != 'inqueue')">{{ printer.queue?.[0]?.name }}
        </td>
        <td v-else></td>
        <td v-if="(printer.queue && printer.queue.length > 0 && printer.queue?.[0]?.status != 'inqueue')">{{
          printer.queue?.[0]?.file_name_original }}</td>
        <td v-else></td>

        <td style="width: 250px;">
          <div v-if="printer.status === 'printing' && printer.queue">
            <div v-for="job in printer.queue" :key="job.id">
              <!-- Display the elapsed time -->
              <p v-if="job.elapsed_time">{{ new Date(job.elapsed_time * 1000).toISOString().substr(11, 8) }}</p>
              <div class="progress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                  :style="{ width: (job.progress || 0) + '%' }" :aria-valuenow="job.progress" aria-valuemin="0"
                  aria-valuemax="100">
                  <!-- job progress set to 2 decimal places -->
                  <p>{{ job.progress ? `${job.progress.toFixed(2)}%` : '' }}</p>
                </div>
              </div>
            </div>
          </div>

          <div
            v-else-if="(printer?.status != 'printing') && (printer.queue && printer.queue.length > 0 && printer.queue?.[0]?.status != 'printing' && printer.queue?.[0]?.status != 'inqueue')">
            <button type="button" class="btn btn-danger"
              @click="releasePrinter(printer.queue?.[0], 3, printer, printer.id, 'error')">Fail</button>
            <button type="button" class="btn btn-secondary"
              @click="releasePrinter(printer.queue?.[0], 1, printer, printer.id, 'ready')">Clear</button>

            <!-- Clear/Rerun dropdown -->
            <div class="dropdown">
              <button class="btn btn-info dropdown-toggle" type="button" id="rerunDropdown" data-bs-toggle="dropdown"
                aria-expanded="false">
                Clear/Rerun
              </button>
              <ul class="dropdown-menu" aria-labelledby="rerunDropdown">
                <li v-for="rerunPrinter in printers" :key="rerunPrinter.id">
                  <a class="dropdown-item"
                    @click="releasePrinter(printer.queue?.[0], 2, rerunPrinter, rerunPrinter.id, 'ready')">{{ rerunPrinter.name
                    }}</a>
                </li>
              </ul>
            </div>
          </div>

        </td>


      </tr>
    </table>
  </div>
</template>

<style scoped>
table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 2px solid #dddddd;
  /* Set border width and color */
  text-align: left;
  padding: 8px;
}

th {
  background-color: #f2f2f2;
}

p {
  margin: 0;
}
</style>