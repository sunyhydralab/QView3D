<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useGetJobs, type Job, useRerunJob } from '@/model/jobs';
import { computed, onMounted, ref, watch } from 'vue';
// import { useGetJobs, type Job } from '@/model/jobs';
// import { computed, onMounted, ref } from 'vue';
const { jobhistory } = useGetJobs()
const { retrieveInfo } = useRetrievePrintersInfo()
const { rerunJob } = useRerunJob()

const printers = ref<Array<Device>>([]) // Get list of open printer threads 
const selectedPrinters = ref<Array<Device>>([])
let jobs = ref<Array<Job>>([])
let filter = ref('') // This will hold the current filter value

let page = ref(1)
let pageSize = ref(10)
let totalJobs = ref(0)

onMounted(async () => {
    try {
        // job history now returns a tuple of joblist and total jobs, not just all the jobs in the database
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        const printerInfo = await retrieveInfo()
        printers.value = printerInfo
    } catch (error) {
        console.error(error)
    }
})

const handleRerun = async (job: Job, printer: Device) => {
    try {
        await rerunJob(job, printer);
        // Fetch the updated list of jobs after rerunning the job
        // so when a job is rerun, the job history is updated
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)

        jobs.value = joblist;
        totalJobs.value = total;
    } catch (error) {
        console.error(error)
    }
}

// watch(pageSize, async (newPageSize) => {
//     jobs.value = []; // Clear the jobs array
//     // Fetch the updated list of jobs after changing the page size
//     const [joblist, total] = await jobhistory(page.value, newPageSize)
//     jobs.value = joblist;
//     totalJobs.value = total;
// })

const changePage = async (newPage: any) => {
    // Prevent the user from going to a page that doesn't exist
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    // Assign the new page value based on the parameter passed in
    page.value = newPage
    jobs.value = []; // Clear the jobs array
    // Fetch the updated list of jobs after changing the page
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
    jobs.value = joblist;
    totalJobs.value = total;
}
// computed property that returns the filtered list of jobs. 
let filteredJobs = computed(() => {
    if (filter.value) {
        return jobs.value.filter(job => job.printer.includes(filter.value))
    } else {
        return jobs.value
    }
})

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer)
    }
}

async function submitFilter() {
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
    jobs.value = joblist;
    totalJobs.value = total;
}
</script>

<template>
    <div class="container">
        <b>Job History View</b>
        <div class="mb-3">
            <br>
            <label for="pageSize" class="form-label">Jobs per page:</label>
            <input id="pageSize" type="number" v-model.number="pageSize" min="1" class="form-control" style="width: auto;">

            <select required multiple>
                <option :value="null">Device: None</option>
                <option v-for="printer in printers" :value="printer" :key="printer.id" @click="appendPrinter(printer)">
                    {{ printer.name }}
                </option>
            </select>
            <br>
            <button @click="submitFilter">Submit Filter</button>
            <div>
                Selected printer(s): <br>
                <p v-for="printer in selectedPrinters">
                    <b>{{ printer.name }}</b> status: {{ printer.status }}<br>
                </p>
            </div>
        </div>
        <table class="table">
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Date Completed</th>
                    <th>Final Status</th>
                    <th>Printer</th>
                    <th>Rerun Job</th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.name">
                    <td>{{ job.id }}</td>
                    <td>{{ job.name }}</td>
                    <td>{{ job.file_name_original }}</td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <td>{{ job.printer }}</td>
                    <td>
                        <div class="dropdown">
                            <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                                data-bs-toggle="dropdown" aria-expanded="false">
                                Rerun Job
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="printerDropdown">
                                <li v-for="printer in printers" :key="printer.id">
                                    <a class="dropdown-item" @click="handleRerun(job, printer)">{{ printer.name }}</a>
                                </li>
                            </ul>
                        </div>
                    </td>
                </tr>

            </tbody>

            <tbody v-else>
                <tr>
                    <td colspan="7">No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink>
                    </td>
                </tr>
            </tbody>
        </table>
        <nav aria-label="Page navigation">
            <ul class="pagination">
                <li class="page-item" :class="{ 'disabled': page <= 1 }">
                    <a class="page-link" href="#" @click.prevent="changePage(page - 1)">Previous</a>
                </li>
                <li class="page-item disabled"><a class="page-link">Page {{ page }} of {{ Math.ceil(totalJobs / pageSize)
                }}</a></li>
                <li class="page-item" :class="{ 'disabled': page >= Math.ceil(totalJobs / pageSize) }">
                    <a class="page-link" href="#" @click.prevent="changePage(page + 1)">Next</a>
                </li>
            </ul>
        </nav>
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