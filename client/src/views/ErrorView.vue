<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { type Issue, useGetIssues, useCreateIssues, useAssignIssue, useDeleteIssue } from '../model/issues'
import { type Job, useGetErrorJobs, useAssignComment, useGetJobFile, useGetFile } from '../model/jobs';
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'

const { jobhistoryError } = useGetErrorJobs()
const { issues } = useGetIssues()
const { createIssue } = useCreateIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { getFileDownload } = useGetJobFile()
const { getFile } = useGetFile()
const { deleteIssue } = useDeleteIssue()

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

let currentJob = ref<Job>()
let isGcodeImageVisible = ref(false)

let filter = ref('')
let filterDropdown = ref(false)
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

        document.addEventListener('click', closeDropdown);

    } catch (error) {
        console.error(error)
    }
})

onBeforeUnmount(() => {
    document.removeEventListener('click', closeDropdown);
});

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

async function submitFilter() {
    filterDropdown.value = false;

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
    issuelist.value = newIssues
    newIssue.value = ''
    showText.value = false
}

/** */

////
const doDeleteIssue = async () => {
    console.log(selectedIssue.value)
    if (selectedIssue.value === undefined) return
    console.log(selectedIssue.value)
    await deleteIssue(selectedIssue.value)
}

const doAssignIssue = async () => {
    if (selectedJob.value === undefined) return
    if (selectedIssue.value !== undefined) {
        await assign(selectedIssue.value.id, selectedJob.value.id)
        console.log(selectedIssue.value.issue)
        selectedJob.value.error = selectedIssue.value!.issue
    }
    await assignComment(selectedJob.value, jobComments.value)
    selectedJob.value.comment = jobComments.value
    selectedIssue.value = undefined
    selectedJob.value = undefined
}

const setJob = async (job: Job) => {
    jobComments.value = job.comment || '';
    selectedJob.value = job;
}

function clearFilter() {
    page.value = 1;
    // pageSize.value = 10;

    selectedPrinters.value = [];
    selectedIssues.value = [];

    if (order.value === 'oldest') {
        order.value = 'newest';
    }
    favoriteOnly.value = false;

    searchJob.value = '';
    searchByJobName.value = true;
    searchByFileName.value = true;

    submitFilter();
}

const closeDropdown = (evt: any) => {
    if (filterDropdown.value && evt.target.closest('.dropdown-card') === null) {
        filterDropdown.value = false;
    }
}

const handleRerun = async (job: Job, printer: Device) => {
    await router.push({
        name: 'SubmitJobVue', // the name of the route to SubmitJob.vue
        params: { job: JSON.stringify(job), printer: JSON.stringify(printer) } // the job and printer to fill in the form
    });
}

const handleEmptyRerun = async () => {
    await router.push({
        name: 'SubmitJobVue'
    })
}

const openGCodeModal = async (job: Job, printerName: string) => {
    currentJob.value = job
    currentJob.value.printer = printerName
    isGcodeImageVisible.value = true
    if (currentJob.value) {
        const file = await getFile(currentJob.value)
        if (file) {
            currentJob.value.file = file
        }
    }
}

// const allSelected = computed({
//     get: () => selectedIssues.value.length > 0 && selectedIssues.value.length === issues.length,
//     set: (value) => {
//         if (value) {
//             selectedIssues.value = issues.slice();
//         } else {
//             selectedIssues.value = [];
//         }
//     }
// });

</script>

<template>
    <!-- gcode image viewer modal -->
    <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true"
        @shown.bs.modal="isGcodeImageVisible = true" @hidden.bs.modal="isGcodeImageVisible = false">
        <div class="modal-dialog modal-dialog-centered modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="gcodeImageModalLabel">
                        <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob!" />
                    </div>
                </div>
            </div>
        </div>
    </div>


    <div class="modal fade" id="assignissueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header d-flex align-items-end">
                    <h5 class="modal-title" id="assignIssueLabel">
                        <b>Create New Issue</b>
                    </h5>

                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form class="p-3 border rounded bg-light mb-3">
                        <div class="mb-3">
                            <label for="newIssue" class="form-label">Enter Issue</label>
                            <input id="newIssue" type="text" placeholder="Enter Issue" v-model="newIssue"
                                class="form-control" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="submit" @click.prevent="doCreateIssue" class="btn btn-primary me-2"
                        v-bind:disabled="!newIssue" data-bs-dismiss="modal">Create Issue</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Delete modal issue -->
    <div class="modal fade" id="deleteissueModal" tabindex="-1" aria-labelledby="deleteIssueLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header d-flex align-items-end">
                    <h5 class="modal-title" id="assignIssueLabel">
                        <b>Delete Issue</b>
                    </h5>

                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="">
                        <div class="mb-3">
                            <label for="issue" class="form-label">Select Issue</label>
                            <select name="issue" id="issue" v-model="selectedIssue" class="form-select" required>
                                <option disabled value="undefined">Select Issue</option>
                                <option v-for="issue in issuelist"  :key="issue.id" :value="issue">
                                    {{ issue.issue }}
                                </option>
                                <!-- <tr  v-for="issue in issuelist"  :key="issue.id">
                                    <td>
                                        <input type="checkbox" v-model="selectedIssue" :value="issue">
                                    </td>
                                    <td>{{ issue.issue }}</td>
                                </tr> -->
                            </select>
                        </div>

                        <!-- <div class="mb-3">
                        <label for="printer" class="form-label">Select Printer</label>
                        <div class="card" style="max-height: 120px; overflow-y: auto;">
                            <ul class="list-unstyled card-body m-0" style="padding-top: .5rem; padding-bottom: .5rem;">
                                <li>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="select-all"
                                            >
                                        <label class="form-check-label" for="select-all">
                                            Select All
                                        </label>
                                    </div>
                                    <div class="border-top"
                                        style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                                </li>
                                <li v-for="issue in issuelist"  :key="issue.id">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" :value="issue"
                                            v-model="selectedIssue" :id="'issue-' + issue.id">
                                        <label class="form-check-label" :for="'issue-' + issue.id">
                                            {{ issue.issue }}
                                        </label>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </div> -->

                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="submit" @click.prevent="doDeleteIssue" class="btn btn-danger me-2"
                        data-bs-dismiss="modal">Delete</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header d-flex align-items-end">
                    <h5 class="modal-title mb-0" id="assignIssueLabel" style="line-height: 1;">Job #{{ selectedJob?.id
                        }}</h5>
                    <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px; line-height: 1;">{{
                        selectedJob?.date }}</h6>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
                        @click="selectedIssue = undefined; selectedJob = undefined;"></button>
                </div>
                <div class="modal-body">
                    <button class="btn btn-primary mb-3" @click="showText = !showText">Create New Issue</button>
                    <form v-if="showText" class="p-3 border rounded bg-light mb-3">
                        <div class="mb-3">
                            <label for="newIssue" class="form-label">Enter Issue</label>
                            <input id="newIssue" v-model="newIssue" type="text" placeholder="Enter Issue"
                                class="form-control" required>
                        </div>
                        <div>
                            <button type="submit" @click.prevent="doCreateIssue" class="btn btn-primary me-2"
                                v-bind:disabled="!newIssue">Submit</button>
                            <button @click.prevent="showText = !showText" class="btn btn-secondary">Cancel</button>
                        </div>
                    </form>
                    <form @submit.prevent="">
                        <div class="mb-3">
                            <label for="issue" class="form-label">Select Issue</label>
                            <select name="issue" id="issue" v-model="selectedIssue" class="form-select" required>
                                <option disabled value="undefined">Select Issue</option>
                                <option v-for="issue in issuelist" :value="issue">
                                    {{ issue.issue }}
                                </option>
                            </select>
                        </div>
                    </form>
                    <div class="form-group mt-3">
                        <label for="exampleFormControlTextarea1">Comments</label>
                        <textarea class="form-control" id="exampleFormControlTextarea1" rows="3"
                            v-model="jobComments"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
                        @click="selectedIssue = undefined; selectedJob = undefined">Close</button>
                    <button type="button" class="btn btn-success" data-bs-dismiss="modal" @click="doAssignIssue">Save
                        Changes</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <b>Error Log</b>
        <div class="d-flex justify-content-center align-items-center" style="margin-bottom: 0.5rem;">
            <div class="d-flex justify-content-center">
                <div style="position: relative;">
                    <button type="button" class="btn btn-primary dropdown-toggle"
                        @click.stop="filterDropdown = !filterDropdown">
                        Filter
                    </button>
                    <form v-show="filterDropdown" class="card dropdown-card p-3">
                        <div class="mb-3">
                            <label for="pageSize" class="form-label">
                                Jobs per page, out of {{ totalJobs }}:
                            </label>
                            <input id="pageSize" type="number" v-model.number="pageSize" min="1" class="form-control">
                        </div>
                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <div class="mb-3">
                            <label class="form-label">Device:</label>
                            <div class="card" style="max-height: 120px; overflow-y: auto;">
                                <ul class="list-unstyled card-body m-0"
                                    style="padding-top: .5rem; padding-bottom: .5rem;">
                                    <li v-for="printer in printers" :key="printer.id">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" :value="printer.id"
                                                v-model="selectedPrinters" :id="'printer-' + printer.id">
                                            <label class="form-check-label" :for="'printer-' + printer.id">
                                                {{ printer.name }}
                                            </label>
                                        </div>
                                    </li>
                                    <div class="border-top"
                                        style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                                    <li>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" value="0"
                                                v-model="selectedPrinters" id="printer-0">
                                            <label class="form-check-label" for="printer-0">
                                                Deregistered printers
                                            </label>
                                        </div>
                                    </li>
                                </ul>
                            </div>
                        </div>
                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <div class="mb-3">
                            <label class="form-label">Issue:</label>
                            <div class="card" style="max-height: 120px; overflow-y: auto;">
                                <ul class="list-unstyled card-body m-0"
                                    style="padding-top: .5rem; padding-bottom: .5rem;">
                                    <li v-for="issue in issuelist" :key="issue.id">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" :value="issue"
                                                v-model="selectedIssues" :id="'issue-' + issue.id">
                                            <label class="form-check-label" :for="'issue-' + issue.id">
                                                {{ issue.issue }}
                                            </label>
                                        </div>
                                    </li>
                                    <div class="border-top"
                                        style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                                    <li>
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" value="0"
                                                v-model="selectedIssues" id="issue-0">
                                            <label class="form-check-label" for="issue-0">
                                                None
                                            </label>
                                        </div>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <div class="mb-3">
                            <label for="searchJob" class="form-label">Search for jobs:</label>
                            <input type="text" id="searchJob" class="form-control" v-model="searchJob">
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="searchByJobName"
                                v-model="searchByJobName" :disabled="isOnlyJobNameChecked"
                                @change="ensureOneCheckboxChecked">
                            <label class="form-check-label" for="searchByJobName">Search by Job Name</label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" id="searchByFileName"
                                v-model="searchByFileName" :disabled="isOnlyFileNameChecked"
                                @change="ensureOneCheckboxChecked">
                            <label class="form-check-label" for="searchByFileName">Search by File Name</label>
                        </div>
                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <label class="form-label">Order:</label>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="order" id="orderNewest" value="newest"
                                v-model="order">
                            <label class="form-check-label" for="orderNewest" @click.stop>Newest to
                                Oldest</label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="order" id="orderOldest" value="oldest"
                                v-model="order">
                            <label class="form-check-label" for="orderOldest">Oldest to Newest</label>
                        </div>
                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <div class="d-flex justify-content-center">
                            <button @click.prevent="submitFilter" class="btn btn-primary me-3">Submit
                                Filter</button>
                            <button @click.prevent="clearFilter" class="btn btn-danger">Clear Filter</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#assignissueModal">
                <i class="fas fa-plus"></i> &nbsp
                Add New Issue
            </button>

            <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#deleteissueModal">
                <i class="fas fa-trash-alt"></i> &nbsp
                Delete Issue
            </button>

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
                    <td>{{ job.name }}</td>
                    <td>{{ job.file_name_original }}</td>
                    <td>{{ job.printer }}</td>
                    <td v-if="job.errorid != null && job.errorid != 0">
                        {{ job.error }}
                    </td>
                    <td v-else>
                    </td>
                    <td>
                        <div class="dropdown">
                            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                <button type="button" id="settingsDropdown" data-bs-toggle="dropdown"
                                    aria-expanded="false" style="background: none; border: none;">
                                    <i class="fas fa-ellipsis"></i>
                                </button>
                                <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                                    <li>
                                        <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                            data-bs-target="#gcodeImageModal" @click="openGCodeModal(job, job.printer)">
                                            <i class="fa-regular fa-image"></i>
                                            <span class="ms-2">Image Viewer</span>
                                        </a>
                                    </li>
                                    <li>
                                        <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                            data-bs-target="#issueModal" @click="setJob(job); showText = false">
                                            <i class="fas fa-comments"></i>
                                            <span class="ms-2">Comments</span>
                                        </a>
                                    </li>
                                    <li>
                                        <a class="dropdown-item d-flex align-items-center"
                                            @click="getFileDownload(job.id)"
                                            :disabled="job.file_name_original.includes('.gcode:')">
                                            <i class="fas fa-download"></i>
                                            <span class="ms-2">Download</span>
                                        </a>
                                    </li>
                                    <li>
                                        <hr class="dropdown-divider">
                                    </li>
                                    <li class="dropdown-submenu">
                                        <a class="dropdown-item d-flex justify-content-between align-items-center"
                                            @click="handleEmptyRerun">
                                            <div class="d-flex align-items-center">
                                                <i class="fa-solid fa-arrow-rotate-right"></i>
                                                <span class="ms-2">Rerun</span>
                                            </div>
                                            <i class="fa-solid fa-chevron-right"></i>
                                        </a>
                                        <ul class="dropdown-menu">
                                            <li v-for="printer in printers" :key="printer.id">
                                                <a class="dropdown-item" @click="handleRerun(job, printer)">
                                                    {{ printer.name }}
                                                </a>
                                            </li>
                                        </ul>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </td>
                </tr>
            </tbody>
            <tbody v-else>
                <tr>
                    <td colspan="6">No jobs with errors found. </td>
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
.dropdown-card {
    position: absolute !important;
    left: 50% !important;
    top: calc(100% + 2px) !important;
    /* Adjust this value to increase or decrease the gap */
    transform: translateX(-50%) !important;
    width: 400px;
    z-index: 1000;
}

.dropdown-submenu {
    position: relative;
    box-sizing: border-box;
}

.dropdown-submenu .dropdown-menu {
    top: -9px;
    left: 99.9%; /* Adjust this value as needed */
    max-height: 200px; /* Adjust this value as needed */
    overflow-y: auto;
}

.dropdown-submenu:hover>.dropdown-menu {
    display: block;
}

.dropdown-item {
    display: flex;
    align-items: center;
    padding-left: .5rem;
}

.dropdown-item i {
    width: 20px;
}

.dropdown-item span {
    margin-left: 10px;
}

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

ul.dropdown-menu.w-100.show li.divider {
    margin-left: 0;
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
</style>
