<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '@/model/ports';
import { onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const { retrieveInfo } = useRetrievePrintersInfo();
const router = useRouter();

let printers = ref<Array<Device>>([]); // Array of all devices. Used to list registered printers on frontend. 
let intervalId: number | undefined

const sendToQueueView = (name: string | undefined) => {
  if (name) {
    router.push({ name: 'QueueViewVue', params: { printerName: name } });
  }
}

// set the status of the printer
const setPrinterStatus = (printer: Device, status: string) => {
  // set the status of the printer
  // to the selected status
  // TODO: implement this
  console.log('Setting status of printer:', printer, 'to:', status);
}

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

     // Then fetch it every 5 seconds
     intervalId = window.setInterval(updatePrinters, 5000)

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

// fail the print job
const failPrint = (printer: Device) => {
  // fail the print job
}

// clear the print job
const clearPrint = (printer: Device) => {
  // clear the print job
}

// rerun the print job
const clearThenRerunPrint = (printer: Device) => {
  // rerun the print job
}

onMounted(async () => {
  try {
    const printerInfo = await retrieveInfo()//list of previously registered printers 
    printers.value = printerInfo; // loads registered printers into registered array 
  } catch (error) {
    console.error(error)
  }
})

</script>

<template>
  <div class="container">
    <b>Home</b>
    <table>
      <!-- This data is taken from the backend in-memory array, NOT the database. Done with threading. -->
      <!-- Perhaps the printer names are displayed and this is drawn from the database, but all of the associated data
              is taken from the in-memory threads and cron updates. 
          -->
      <tr>
        <th>Printer name</th>
        <th>Status</th>
        <th>Job Name</th>
        <th>File</th>
        <th>Progress</th>
      </tr>
      <div v-if="printers.length === 0">No printers available. Either register a printer <RouterLink to="/registration">
          here</RouterLink>, or restart the server.</div>
      <tr v-for="printer in printers" :key="printer.name">
        <td><button type="button" class="btn btn-link" @click="sendToQueueView(printer.name)">{{ printer.name }}</button>
        </td>
        <td>
          <select v-model="printer.status">
            <option value="ready" @click="setPrinterStatus(printer, 'ready')">Ready</option>
            <option value="error" @click="setPrinterStatus(printer, 'error')">Error</option>
            <option value="offline" @click="setPrinterStatus(printer, 'offline')">Offline</option>
            <option value="printing" @click="setPrinterStatus(printer, 'printing')">Printing</option>
            <option value="complete" @click="setPrinterStatus(printer, 'complete')">Complete</option>
          </select>
        </td>
        <td>{{ printer.queue?.[0]?.name }}</td>
        <td>{{ printer.queue?.[0]?.file_name }}</td>
        <td>
          <!-- if printer is still printing, show progress bar -->

          <div v-if="printer.status === 'printing'">
            <div class="progress">
              <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 25%"
                aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">
                <p>
                  <!-- printers progress % -->
                  <!-- this will be the style="width: 25%" -->
                </p>
              </div>
            </div>
          </div>
          <div v-else>
            <button type="button" class="btn btn-danger" @click="failPrint(printer)">Fail</button>
            <button type="button" class="btn btn-secondary" @click="clearPrint(printer)">Clear</button>
            <button type="button" class="btn btn-info" @click="clearThenRerunPrint(printer)">Clear/Rerun</button>
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