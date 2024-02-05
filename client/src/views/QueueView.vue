<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRetrievePrintersInfo, type Device } from '../model/ports'
const { retrieveInfo } = useRetrievePrintersInfo()

const printers = ref<Array<Device>>([]) // Get list of open printer threads 


onMounted(async () => {
  try {
    printers.value = await retrieveInfo()
  } catch (error) {
    console.error('There has been a problem with your fetch operation:', error)
  }
})


</script>
<template>
  <div class="container">
    <p>Queue View</p>

    <div class="dropdown" v-for="printer in printers" :key="printer.id">
      <button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton">
        {{ printer.name }}
      </button>
      <div class="dropdown-menu show" aria-labelledby="dropdownMenuButton">
        <!-- <div v-for="job in printer.queue" :key="job.name" class="dropdown-item" href="#">{{job.name}}</div> -->
        <table>
          <!-- This data is taken from the backend in-memory array, NOT the database. Done with threading. -->
          <!-- Perhaps the printer names are displayed and this is drawn from the database, but all of the associated data
              is taken from the in-memory threads and cron updates. 
          -->
            <tr>
                <th>Cancel</th> 
                <th>Rerun</th>
                <th>Position</th>
                <th>Bump</th>
                <th>Job Name</th>
                <th>File</th>
                <th>Time added</th>
                <th>Flag</th>
            </tr>
            <tr v-for="job in printer.queue">
                <th></th> 
                <th></th>
                <th></th>
                <th></th>
                <th>{{ job.name }}</th>
                <th>{{ job.file_name }}</th>
                <th>{{ job.date }}</th>
                <th>{{ job.status }}</th>
            </tr>
        </table>
      </div>
      

    </div>

  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.dropdown {
  width: auto;
  display: flex;
  flex-direction: column;
  align-items: center; /* Center content horizontally */
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

.dropdown-toggle {
  width: 100%;
  text-align: left;
  padding: 8px;
  margin-bottom: 20px; 
}
</style>
