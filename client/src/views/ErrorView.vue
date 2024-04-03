<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { type Issue, useGetIssues, useCreateIssues, useAssignIssue } from '../model/issues'
import { type Job, useGetErrorJobs, useAssignComment } from '../model/jobs';
import { computed, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const { jobhistoryError } = useGetErrorJobs()
const { issues } = useGetIssues()
const { createIssue } = useCreateIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()

const showText = ref(false)
const newIssue = ref('')
const selectedIssue = ref<Issue>()
const selectedJob = ref<Job>()
const selectedIssues = ref<Array<number>>([])

const selectedPrinters = ref<Array<Number>>([])
const selectedJobs = ref<Array<Job>>([]);
const searchJob = ref(''); // This will hold the current search query
const searchByJobName = ref(true);
const searchByFileName = ref(true);

const router = useRouter();

let jobs = ref<Array<Job>>([])
let issuelist = ref<Array<Issue>>([])

let filter = ref('')
let oldestFirst = ref<boolean>(false)
let order = ref<string>('newest')
let favoriteOnly = ref<boolean>(false)
let jobComments = ref('')

let page = ref(1)
let pageSize = ref(10)
let totalJobs = ref(0)
let totalPages = ref(1)

let searchCriteria = ref('');
const isOnlyJobNameChecked = computed(() => searchByJobName.value && !searchByFileName.value);
const isOnlyFileNameChecked = computed(() => !searchByJobName.value && searchByFileName.value);

// computed property that returns the filtered list of jobs. 
let filteredJobs = computed(() => {
    if (filter.value) {
        return jobs.value.filter(job => job.printer.includes(filter.value))
    } else {
        return jobs.value
    }
})


onMounted(async () => {
    try {
        const retrieveissues = await issues()
        issuelist.value = retrieveissues

        const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistoryError(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        totalPages.value = Math.ceil(total / pageSize.value);
        totalPages.value = Math.max(totalPages.value, 1);

        console.log(jobs.value)

    } catch (error) {
        console.error(error)
    }
})

const changePage = async (newPage: any) => {
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    selectedJobs.value = [];


    page.value = newPage
    jobs.value = []
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistoryError(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value)
    jobs.value = joblist;
    totalJobs.value = total;
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer.id!)) {
        selectedPrinters.value.push(printer.id!)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer.id)
    }
}

async function submitFilter() {
    jobs.value = []
    oldestFirst.value = order.value === 'oldest';
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    if (searchByJobName.value && !searchByFileName.value) {
        searchCriteria.value = 'searchByJobName';
    } else if (!searchByJobName.value && searchByFileName.value) {
        searchCriteria.value = 'searchByFileName';
    } else {
        searchCriteria.value = searchJob.value;
    }

    // Get the total number of jobs first, without considering the page number
    const [, total] = await jobhistoryError(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value, selectedIssues.value);
    totalJobs.value = total;

    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);
    totalPages.value = Math.max(totalPages.value, 1);

    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    // Now fetch the jobs for the current page
    const [joblist] = await jobhistoryError(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value, selectedIssues.value);
    jobs.value = joblist;

    selectedJobs.value = [];
}

const ensureOneCheckboxChecked = () => {
    if (!searchByJobName.value && !searchByFileName.value) {
        searchByJobName.value = true;
    }
}

const doCreateIssue = async () => {
    await createIssue(newIssue.value)
    const newIssues = await issues()
    console.log(newIssues)
    issuelist.value = newIssues
    newIssue.value = ''
    showText.value = false
}

const doAssignIssue = async () => {
    if (selectedJob.value === undefined) return
    if(selectedIssue.value !== undefined){
        await assign(selectedIssue.value.id, selectedJob.value.id)
        selectedJob.value.error = selectedIssue.value!.issue
    }
    await assignComment(selectedJob.value, jobComments.value)
    selectedJob.value.comment = jobComments.value
    selectedIssue.value = undefined
    selectedJob.value = undefined
}


function appendIssue(issue: Issue) {
    if (!selectedIssues.value.includes(issue.id!)) {
        selectedIssues.value.push(issue.id!)
    } else {
        selectedIssues.value = selectedIssues.value.filter(p => p !== issue.id)
    }
}


function appendNullIssue() {
    if (!selectedIssues.value.includes(0)) {
        selectedIssues.value.push(0)
    } else {
        selectedIssues.value = selectedIssues.value.filter(p => p !== 0)
    }
}

function appendNullPrinter() {
    if (!selectedPrinters.value.includes(0)) {
        selectedPrinters.value.push(0)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== 0)
    }
}

const setJob = async(job: Job) => {
    jobComments.value = job.comment || '';
    selectedJob.value = job; 
}
</script>

<template>

    <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
        data-bs-backdrop="static">

        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="assignIssueLabel">Job#{{ selectedJob?.id }}</h5>
                    <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px">{{ selectedJob?.date }}</h6>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close" @click="selectedIssue = undefined; selectedJob = undefined"></button>
                </div>

                <!-- Create new issue -->
                <button class="btn btn-primary" @click="showText = !showText">Create New Issue</button>
                <form v-if="showText == true" class="p-3">
                    <div class="mb-3">
                        <label for="newIssue" class="form-label">Enter Issue</label>
                        <input id="newIssue" v-model="newIssue" type="text" placeholder="Enter Issue"
                            class="form-control" required>
                    </div>
                    <div>
                        <button type="submit" @click="doCreateIssue" class="btn btn-primary me-2">Submit</button>
                        <button @click="showText = !showText" class="btn btn-secondary">Cancel</button>
                    </div>
                </form>

                <div class="modal-body">
                    <p>
                    <form class="mt-3" @submit.prevent="">
                        <div class="mb-3">
                            <label for="issue" class="form-label">Select Issue</label>
                            <select name="issue" id="issue" v-model="selectedIssue" class="form-select" required>
                                <option value="null" disabled>Select Issue</option> <!-- Default option -->
                                <option v-for="issue in issuelist" :value="issue">
                                    {{ issue.issue }}
                                </option>
                            </select>
                        </div>
                    </form>
                    <div class="form-group">
                        <label for="exampleFormControlTextarea1">Comments</label>
                        <textarea class="form-control" id="exampleFormControlTextarea1" rows="3" v-model="jobComments"></textarea>
                    </div>


                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
                        @click="selectedIssue = undefined; selectedJob = undefined">Close</button>
                    <button type="button" class="btn btn-success" data-bs-dismiss="modal" @click="doAssignIssue">Save Changes</button>
                </div>
            </div>
        </div>

    </div>

    <div class="container">
        <b>Error Log</b>
        <div class="container-fluid mb-2 p-2 border rounded">
            <div class="row justify-content-center">
                <div class="col-md-3 d-flex align-items-start justify-content-between">
                    <label for="pageSize" class="form-label mx-2" style="white-space: nowrap;">Jobs per page:</label>
                    <input id="pageSize" type="number" v-model.number="pageSize" min="1" class="form-control mx-2">
                    <label class="form-label mx-2">/&nbsp;{{ totalJobs }}</label>
                </div>
                <div class="col-md-3 d-flex align-items-start justify-content-between">
                    <label class="form-label mx-2">Device:</label>
                    <div class="dropdown w-100 mx-2">
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
                            <li class="dropdown-divider"></li>
                            <li>
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input" type="checkbox" id="deregistered-printers"
                                        @click="appendNullPrinter">
                                    <label class="form-check-label" for="deregistered-printers"
                                        @click="appendNullPrinter">
                                        Deregistered printers
                                    </label>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col-md-3 d-flex align-items-start justify-content-between">
                    <label class="form-label mx-2">Issue:</label>
                    <div class="dropdown w-100 mx-2">
                        <button class="btn btn-secondary dropdown-toggle w-100" type="button" id="dropdownMenuButton"
                            data-bs-toggle="dropdown" aria-expanded="false">
                            Select Issue
                        </button>
                        <ul class="dropdown-menu w-100" aria-labelledby="dropdownMenuButton">
                            <li v-for="issue in issuelist" :key="issue.id">
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input" type="checkbox" :value="issue"
                                        @change="appendIssue(issue)" :id="'printer-' + issue.id">
                                    <label class="form-check-label" :for="'printer-' + issue.id">
                                        {{ issue.issue }}
                                    </label>
                                </div>
                            </li>
                            <li class="dropdown-divider"></li>
                            <li>
                                <div class="form-check" @click.stop>
                                    <input class="form-check-input" type="checkbox" id="deregistered-printers"
                                        @click="appendNullIssue">
                                    <label class="form-check-label" for="deregistered-printers">
                                        None
                                    </label>
                                </div>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="col-md-3">
                    <div class="row mb-1">
                        <div class="col-12">
                            <input type="text" v-model="searchJob" placeholder="Search for jobs" class="form-control">
                        </div>
                    </div>
                    <div class="row mb-1">
                        <div class="col-12">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="searchByJobName"
                                    v-model="searchByJobName" :disabled="isOnlyJobNameChecked"
                                    @change="ensureOneCheckboxChecked">
                                <label class="form-check-label" for="searchByJobName">
                                    Search by Job Name
                                </label>
                            </div>
                        </div>
                    </div>
                    <div class="row mb-1">
                        <div class="col-12">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="searchByFileName"
                                    v-model="searchByFileName" :disabled="isOnlyFileNameChecked"
                                    @change="ensureOneCheckboxChecked">
                                <label class="form-check-label" for="searchByFileName">
                                    Search by File Name
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row w-100" style="margin-bottom: 0.5rem;">
            <div class="col-10 text-center">
                <button @click="submitFilter" class="btn btn-primary">Submit Filter</button>
            </div>
            <div class="col-1 text-end" style="padding-right: 0">
            </div>
        </div>

        <table class="table">
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Printer</th>
                    <th>Issue</th>
                    <th>Actions</th>

                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td>{{ job.id }}</td>
                    <td>
                        <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                            <div>{{ job.name }}</div>
                        </div>
                    </td>
                    <td>
                        {{ job.file_name_original }}
                    </td>
                    <td>{{ job.printer }}</td>
                    <td v-if="job.errorid != null && job.errorid!=0">
                        {{ job.error }}
                    </td>
                    <td v-else>
                    </td>
                    <td>
                        <button data-bs-toggle="modal" data-bs-target="#issueModal" @click="setJob(job)">View
                            Issue</button>
                    </td>

                </tr>
            </tbody>
            <tbody v-else>
                <tr>
                    <td colspan="8">No jobs found. Submit your first job <RouterLink to="/submit">here!</RouterLink>
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
.truncate-name {
    max-width: 200px;
    /* Adjust this value as needed */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.truncate-file {
    max-width: 300px;
    /* Adjust this value as needed */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.grid-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 10px;
}

.header {
    border: 1px solid #e0e0e0;
    padding-left: 10px;
    padding-right: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    background-color: #f2f2f2;
}

.header h5 {
    text-decoration: underline;
}

.job {
    border: 1px solid #e0e0e0;
    padding: 10px;
    border-radius: 5px;
}

.offcanvas {
    width: 700px;
}

.offcanvas-btn-box {
    transition: transform .3s ease-in-out;
    position: fixed;
    top: 50%;
    right: 0;
    z-index: 1041;
}

.offcanvas-end {
    border-left: 0;
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

button {
    margin: 5px;
}
</style>