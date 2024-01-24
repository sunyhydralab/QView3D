<script setup lang="ts">
  import { useRetrievePrinters, type Device } from '@/model/ports';
import { onMounted, ref } from 'vue';
  const {retrieve} = useRetrievePrinters(); 

  let devices = ref<Array<Device>>([]); // Array of all devices. Used to list registered printers on frontend. 

  onMounted(async () => {
    try{
        const registeredList = await retrieve()//list of previously registered printers 
        devices.value = registeredList; // loads registered printers into registered array 
    }catch(error){
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
            <tr v-for="device in devices">
                <th>{{ device.name }}</th> 
                <th></th>
                <th></th>
                <th></th>
                <th></th>
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
</style>