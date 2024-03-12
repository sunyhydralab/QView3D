<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { useGetJobs, type Job, useRerunJob, useGetJobFile, useDeleteJob, useClearSpace } from '../model/jobs';
import { computed, onMounted, ref } from 'vue';

const { jobhistory } = useGetJobs()
const { rerunJob } = useRerunJob()
const { getFile } = useGetJobFile()
const { deleteJob } = useDeleteJob()
const { clearSpace } = useClearSpace()

const selectedPrinters = ref<Array<Device>>([])
const selectedJobs = ref<Array<Job>>([]);
const deleteModalTitle = computed(() => `Deleting ${selectedJobs.value.length} job(s) from database!`);

let jobs = ref<Array<Job>>([])
let filter = ref('')
let oldestFirst = ref<boolean>(false)
let order = ref<string>('newest')

let page = ref(1)
let pageSize = ref(10)
let totalJobs = ref(0)
let totalPages = ref(1)
let selectAllCheckbox = ref(false);

let modalTitle = ref('');
let modalMessage = ref('');
let modalAction = ref('');

let filteredJobs = computed(() => {
    if (filter.value) {
        return jobs.value.filter(job => job.printer.includes(filter.value))
    } else {
        return jobs.value
    }
})

onMounted(async () => {
    try {
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        totalPages.value = Math.ceil(total / pageSize.value);
        totalPages.value = Math.max(totalPages.value, 1);
    } catch (error) {
        console.error(error)
    }
})

const handleRerun = async (job: Job, printer: Device) => {
    try {
        await rerunJob(job, printer);
        const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)

        jobs.value = joblist;
        totalJobs.value = total;
    } catch (error) {
        console.error(error)
    }
}

const changePage = async (newPage: any) => {
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    selectedJobs.value = [];
    selectAllCheckbox.value = false;

    page.value = newPage
    jobs.value = []
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value)
    jobs.value = joblist;
    totalJobs.value = total;
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer)
    }
}

async function submitFilter() {
    jobs.value = []
    oldestFirst.value = order.value === 'oldest';
    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];

    const [, total] = await jobhistory(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value);
    totalJobs.value = total;

    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);
    totalPages.value = Math.max(totalPages.value, 1);

    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    const [joblist] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value);
    jobs.value = joblist;

    selectedJobs.value = [];
    selectAllCheckbox.value = false;
}


const confirmDelete = async () => {
    const deletionPromises = selectedJobs.value.map(job => deleteJob(job));
    await Promise.all(deletionPromises);

    const printerIds = selectedPrinters.value.map(p => p.id).filter(id => id !== undefined) as number[];
    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value);
    jobs.value = joblist;
    totalJobs.value = total;

    selectedJobs.value = [];
    selectAllCheckbox.value = false;
}

const selectAllJobs = () => {
    if (selectAllCheckbox.value) {
        const newSelectedJobs = filteredJobs.value.filter(job => !selectedJobs.value.includes(job));
        selectedJobs.value = [...selectedJobs.value, ...newSelectedJobs];
    } else {
        selectedJobs.value = selectedJobs.value.filter(job => !filteredJobs.value.includes(job));
    }
}

async function clear() {
    await clearSpace()
    // might need a fix here
    submitFilter()
}

const openModal = (title: any, message: any, action: any) => {
    modalTitle.value = title;
    modalMessage.value = message;
    modalAction.value = action;
};

</script>

<template>
    <div class="container">

        <div class="modal fade" id="exampleModal" tabindex="-1" aria-labelledby="exampleModalLabel" aria-hidden="true"
            data-bs-backdrop="static">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="exampleModalLabel">{{ modalTitle }}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p v-html="modalMessage"></p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button v-if="modalAction === 'confirmDelete'" type="button" class="btn btn-danger"
                            data-bs-dismiss="modal" @click="confirmDelete">Delete</button>
                        <button v-if="modalAction === 'clear'" type="button" class="btn btn-danger"
                            data-bs-dismiss="modal" @click="clear">Clear Space</button>
                    </div>
                </div>
            </div>
        </div>

        <h2 class="mb-2 text-center">Job History View</h2>
        <div class="container-fluid mb-2 p-2 border rounded">
            <div class="row justify-content-center">

                <div class="col d-flex align-items-center justify-content-between">
                    <label for="pageSize" class="form-label my-auto" style="white-space: nowrap;">Jobs per page:</label>
                    <input id="pageSize" type="number" v-model.number="pageSize" min="1"
                        class="form-control mx-2 my-auto">
                    <label class="my-auto">/&nbsp;{{ totalJobs }}</label>
                </div>

                <div class="col d-flex align-items-center justify-content-between">
                    <div class="d-flex align-items-center">
                        <label class="form-label">Device:</label>
                        <div style="width: 10px;"></div> <!-- This div will create a white space -->
                    </div>
                    <div class="dropdown w-100">
                        <button class="btn btn-secondary dropdown-toggle w-100" type="button" id="dropdownMenuButton"
                            data-bs-toggle="dropdown" aria-expanded="false">
                            Select Printer
                        </button>
                        <ul class="dropdown-menu w-100" aria-labelledby="dropdownMenuButton">
                            <li v-for="printer in printers" :key="printer.id">
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input" type="checkbox" :value="printer"
                                        @change="appendPrinter(printer)" :id="'printer-' + printer.id">
                                    <label class="form-check-label" :for="'printer-' + printer.id">
                                        {{ printer.name }}
                                    </label>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col d-flex align-items-center">
                    <label class="form-label d-flex align-items-center">Order:</label>
                    <div style="padding-left: 1rem;">
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="order" id="orderNewest" value="newest"
                                v-model="order">
                            <label class="form-check-label" for="orderNewest">
                                Newest to Oldest
                            </label>
                        </div>
                        <div class="form-check">
                            <input class="form-check-input" type="radio" name="order" id="orderOldest" value="oldest"
                                v-model="order">
                            <label class="form-check-label" for="orderOldest">
                                Oldest to Newest
                            </label>
                        </div>
                    </div>
                </div>

                <div class="col d-flex align-items-center justify-content-between">
                    <button @click="clear" class="btn btn-danger w-100">Clear Space</button>
                </div>

            </div>
        </div>
        <div class="row w-100" style="margin-bottom: 0.5rem;">
            <div class="col-1 text-start" style="padding-left: 0">
                <button type="button"
                    @click="openModal(deleteModalTitle, 'Are you sure you want to delete these jobs? This action cannot be <b>undone</b>.', 'confirmDelete')"
                    class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#exampleModal"
                    :disabled="selectedJobs.length === 0">
                    <i class="fas fa-trash-alt"></i>
                </button>

            </div>
            <div class="col-10 text-center">
                <button @click="submitFilter" class="btn btn-primary">Submit Filter</button>
            </div>
            <div class="col-1">
                <!-- Empty column to push the other columns to the left -->
                <!-- maybe put clear space here?? would be above the rerun job column -->
            </div>
        </div>

        <table class="table">
            <thead>
                <tr>
                    <th class="col-checkbox">
                        <input type="checkbox" @change="selectAllJobs" v-model="selectAllCheckbox">
                    </th>
                    <th class="col-job-id">Job ID</th>
                    <th class="col-job-title">Job Title</th>
                    <th class="col-file">File</th>
                    <th class="col-date">Date Completed</th>
                    <th class="col-status">Final Status</th>
                    <th class="col-printer">Printer</th>
                    <th class="col-rerun">Rerun Job</th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td>
                        <input type="checkbox" v-model="selectedJobs" :value="job">
                    </td>
                    <td>{{ job.id }}</td>
                    <td>{{ job.name }}</td>
                    <td>
                        {{ job.file_name_original }}
                        <button class="btn btn-secondary download" @click="getFile(job.id)"
                            :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fas fa-download"></i>
                        </button>
                    </td>
                    <td>{{ job.date }}</td>
                    <td>{{ job.status }}</td>
                    <td>{{ job.printer }}</td>
                    <td>
                        <div class="dropdown">
                            <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                                data-bs-toggle="dropdown" aria-expanded="false"
                                :disabled="job.file_name_original.includes('.gcode:')">
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
                <li class="page-item disabled"><a class="page-link">Page {{ page }} of {{ totalPages }}</a></li>
                <li class="page-item" :class="{ 'disabled': page >= totalPages }">
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

.col-checkbox {
    width: 1vh;
}

.col-job-id {
    width: 8vh;
}

.col-job-title {
    width: 20vh;
}

.col-file {
    width: 35vh;
}

.col-date {
    width: 26vh;
    overflow-x: auto;
    /* Add a horizontal scrollbar if necessary */
    white-space: nowrap;
    /* Prevent the content from wrapping to the next line */
}

.col-status {
    width: 12vh;
}

.col-printer {
    width: 20vh;
}

.col-rerun {
    width: 5vh;
}

ul.dropdown-menu.w-100.show li {
    margin-left: 1rem;
}

.form-check-input:focus,
.form-control:focus {
    outline: none;
    box-shadow: none;
    border-color: #dee2e6;
}

label.form-check-label {
    cursor: pointer;
}

.download {
    float: right;
}
</style>