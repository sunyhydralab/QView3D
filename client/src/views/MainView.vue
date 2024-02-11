<script setup lang="ts">
import { useRetrievePrintersInfo, useSetStatus, type Device } from '@/model/ports';
import {type Job, useRemoveJob, useRerunJob} from '@/model/jobs';
import { onMounted, ref, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useRetrievePrintersInfo, type Device } from '@/model/ports';
import { onMounted, onUnmounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const { retrieveInfo } = useRetrievePrintersInfo();
const { setStatus } = useSetStatus();
const { removeJob } = useRemoveJob()
const { rerunJob } = useRerunJob()

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
     // Then fetch it every 5 seconds
     intervalId = window.setInterval(updatePrinters, 5000)

  } catch (error) {
    console.error(error)
  }
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
  setTimeout(() => {
      // Using setTimeout to ensure the value is reset after the change event is processed
      const selectElement = document.querySelector('select');
      if (selectElement) {
        (selectElement as HTMLSelectElement).value = '';
      }
    });
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

const releasePrinter = async (job: Job | undefined, key: number, printer: Device) => {
  // setPrinterStatus(printer, 'ready')
  if(key==2){
    setPrinterStatus(printer, 'error')
  }else{
    setPrinterStatus(printer, 'ready')
  }

  if (job) {
    await removeJob(job, key);
  }
  if(key == 3){
    await rerunJob(job, printer)
  }

}

</script>

<template>
  <div class="container">
    <b>Home</b>
    <table>
      <tr>
        <th>Printer name</th>
        <th>Printer Status</th>
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
          <p>{{ printer.status }}</p>
          <select @change="setPrinterStatus(printer, ($event.target as HTMLSelectElement).value)">
            <option value="">Change Status</option> <!-- Default option -->
            <option value="offline">Turn Offline</option>
            <option value="ready">Bring Online</option>
          </select>
        </td>

        <td>{{ printer.status === 'printing' || printer.status==='complete' ? printer.queue?.[0].name : '' }}</td>
        <td>{{ printer.status === 'printing' || printer.status==='complete'? printer.queue?.[0].file_name_original : '' }}</td>

        <td>
          <div v-if="printer.status === 'printing'">
            <div class="progress">
              <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 25%"
                aria-valuenow="25" aria-valuemin="0" aria-valuemax="100">
                <p>
                </p>
              </div>
            </div>
          </div>

            <div v-else-if="printer.status === 'complete'">
              <button type="button" class="btn btn-danger" @click="releasePrinter(printer.queue?.[0], 2, printer)">Fail</button>
              <button type="button" class="btn btn-secondary" @click="releasePrinter(printer.queue?.[0], 1, printer)">Clear</button>
              <button type="button" class="btn btn-info" @click="releasePrinter(printer.queue?.[0], 3, printer)">Clear/Rerun</button>
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