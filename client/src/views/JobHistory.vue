<script setup lang="ts">
import { useGetJobs, type Job } from '@/model/jobs';
import { onMounted, ref } from 'vue';
const { jobhistory } = useGetJobs()

let jobs = ref<Array<Job>>([])

onMounted(async () => {
    try {
        const joblist = await jobhistory(); // Retrieve jobs from database. TASK FOR LATER: ONLY PORT 20 AT A TIME, INTRODUCE PAGING 
        jobs.value = joblist; // Bring job array in-memory 
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
            <tr>
                <th>Job Title</th>
                <th>File</th>
                <th>Date Completed</th>
                <th>Final Status</th>
                <th>Printer</th>
                <th>Rerun Job</th>
            </tr>
            <div v-if="jobs.length > 0">
                <tr v-for="job in jobs">
                    <th>{{ job.name }}</th>
                    <th>{{ job.file }}</th>
                    <th>{{ job.date }}</th>
                    <th>{{ job.status }}</th>
                    <th>{{ job.printer }}</th>
                    <th><button class="rerun"></button></th>
                </tr>
            </div>
            <div v-else>
                No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink>
            </div>
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