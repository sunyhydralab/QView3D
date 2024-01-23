<script setup lang="ts">
import test from 'node:test';

    let jobs = [{
        "name": "test job",
        "file": "test.gcode",
        "date": "date",
        "status": "completed",
        "printer": 6
    },
    {
        "name": "test job2",
        "file": "test2.gcode",
        "date": "date2",
        "status": "completed",
        "printer": 4
    },
    ]
</script>

<template>
    <div class="container">
        <b>Job History View</b>
        <table>
        <tr>
            <th>Job Title</th>
            <th>File</th>
            <th>Date Completed</th>
            <th>Final Status</th>
            <th>Printer</th>
            <th>Rerun Job</th>
        </tr>
        <tr v-for="job in jobs">
            <th>{{ job.name }}</th>
            <th>{{ job.file }}</th>
            <th>{{ job.date }}</th>
            <th>{{ job.status }}</th>
            <th>{{ job.printer }}</th>
            <th><button class="rerun"></button></th>
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

  .rerun{
    width: 5vh; 
    height: 5vh; 
  }
</style>