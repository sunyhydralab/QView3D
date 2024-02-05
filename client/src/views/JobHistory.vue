<script setup lang="ts">
import { useGetJobs, type Job } from '@/model/jobs';
import { onMounted, ref } from 'vue';
const { jobhistory } = useGetJobs()

let jobs = ref<Array<Job>>([])

onMounted(async () => {
    try {
        const joblist = await jobhistory(); // Retrieve jobs from database. TASK FOR LATER: ONLY PORT 20 AT A TIME, INTRODUCE PAGING 
        // jobs.value = joblist; // Bring job array in-memory 
        jobs.value = joblist.jobs;
        console.log(joblist)
    } catch (error) {
        console.error(error)
    }
})
</script>

<template>
    <div class="container">
        <b>Job History View</b>
        <table>
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Date Completed</th>
                    <th>Final Status</th>
                    <th>Printer</th>
                    <th>Rerun Job</th>
                </tr>
            </thead>
            <tbody v-if="jobs.length > 0">
                <tr v-for="job in jobs" :key="job.name">
                    <td>{{ job.name }}</td>
                    <td>{{ job.file_name }}</td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <!-- FIX THIS ERROR -->
                    <td>{{ job.printer }}</td>
                    <td><button class="rerun"></button></td>
                </tr>
            </tbody>
            <tbody v-else>
                <tr>
                    <td colspan="6">No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink></td>
                </tr>
            </tbody>
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

.rerun {
    width: 5vh;
    height: 5vh;
}
</style>