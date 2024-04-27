<script setup lang="ts">
import { printers, type Device } from '../model/ports'
import { type Issue, useGetIssues, useCreateIssues, useAssignIssue, useDeleteIssue } from '../model/issues'
import { type Job, useGetErrorJobs, useAssignComment, useGetJobFile, useGetFile, useRemoveIssue, isLoading } from '../model/jobs';
import { computed, onBeforeUnmount, onMounted, ref, watchEffect } from 'vue';
import { useRouter } from 'vue-router';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import VueDatePicker from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

const { jobhistoryError } = useGetErrorJobs()
const { issues } = useGetIssues()
const { createIssue } = useCreateIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { getFileDownload } = useGetJobFile()
const { getFile } = useGetFile()
const { deleteIssue } = useDeleteIssue()
const { removeIssue } = useRemoveIssue()

const showText = ref(false)
const newIssue = ref('')
const selectedIssue = ref<Issue>()
const selectedIssueId = ref<number>()
const selectedJob = ref<Job>()
const selectedIssues = ref<Array<number>>([])

const selectedPrinters = ref<Array<Number>>([])
const selectedJobs = ref<Array<Job>>([]);
const searchJob = ref(''); // This will hold the current search query
const searchByJobName = ref(true);
const searchByFileName = ref(true);

const date = ref(null as Date | null);
let startDateString = ref<string>('');
let endDateString = ref<string>('');

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
        isLoading.value = true
        const retrieveissues = await issues()
        issuelist.value = retrieveissues

        const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistoryError(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        isLoading.value = false 

        totalPages.value = Math.ceil(total / pageSize.value);
        totalPages.value = Math.max(totalPages.value, 1);

        console.log(jobs.value)

        document.addEventListener('click', closeDropdown);

        const imageModal = document.getElementById('gcodeImageModal');

        imageModal?.addEventListener('hidden.bs.modal', () => {
            isGcodeImageVisible.value = false;
        });

    } catch (error) {
        console.error(error)
    }
})

onBeforeUnmount(() => {
    document.removeEventListener('click', closeDropdown);
});

watchEffect(() => {
    if (selectedJob.value) {
        const issueName = selectedJob.value.error;
        const issue = issuelist.value.find((issue: any) => issue.issue === issueName);
        selectedIssueId.value = issue ? issue.id : undefined;
    }
});

const changePage = async (newPage: any) => {
    isLoading.value = true
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    selectedJobs.value = [];

    page.value = newPage
    jobs.value = []
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistoryError(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value, selectedIssues.value, startDateString.value, endDateString.value)
    jobs.value = joblist;
    totalJobs.value = total;
    isLoading.value = false
}
async function submitFilter() {
    isLoading.value = true
    filterDropdown.value = false;

    if (date.value && Array.isArray(date.value)) {
        const dateArray = date.value as unknown as Date[];
        if (dateArray.length >= 2) {
            startDateString.value = new Date(dateArray[0].setHours(0, 0, 0, 0)).toISOString();
            if (dateArray[1] != null) {
                endDateString.value = new Date(dateArray[1].setHours(23, 59, 59, 999)).toISOString();
            } else {
                endDateString.value = new Date(dateArray[0].setHours(23, 59, 59, 999)).toISOString();
            }
        }
    }

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
    console.log("ISSUES, " + selectedIssues.value)

    // Get the total number of jobs first, without considering the page number
    const [, total] = await jobhistoryError(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value, selectedIssues.value, startDateString.value, endDateString.value);
    totalJobs.value = total;

    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);
    totalPages.value = Math.max(totalPages.value, 1);

    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    // Now fetch the jobs for the current page
    const [joblist] = await jobhistoryError(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value, selectedIssues.value, startDateString.value, endDateString.value);
    jobs.value = joblist;

    selectedJobs.value = [];

    date.value = null;
    isLoading.value = false
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

    date.value = null;

    startDateString.value = '';
    endDateString.value = '';

    submitFilter();
}

const ensureOneCheckboxChecked = () => {
    if (!searchByJobName.value && !searchByFileName.value) {
        searchByJobName.value = true;
    }
}

const doCreateIssue = async () => {
    isLoading.value = true
    await createIssue(newIssue.value)
    const newIssues = await issues()
    issuelist.value = newIssues
    newIssue.value = ''
    showText.value = false
    isLoading.value = false
}

const doDeleteIssue = async () => {
    isLoading.value = true  
    if (selectedIssue.value === undefined) return
    await deleteIssue(selectedIssue.value)
    const newIssues = await issues()
    issuelist.value = newIssues
    submitFilter()
    isLoading.value = false
}

const doAssignIssue = async () => {
    if (selectedJob.value === undefined) return
    const selectedIssueObject = issuelist.value.find((issue: any) => issue.id === selectedIssueId.value);
    if (selectedIssueObject == undefined) {
        await removeIssue(selectedJob.value)
        submitFilter();
    }
    if (selectedIssueObject !== undefined) {
        await assign(selectedIssueObject.id, selectedJob.value.id)
        selectedJob.value.errorid = selectedIssueObject.id
        selectedJob.value.error = selectedIssueObject.issue
    }
    selectedJob.value.comment = jobComments.value
    await assignComment(selectedJob.value, jobComments.value)
    selectedIssueId.value = undefined
    selectedJob.value = undefined
}

const setJob = async (job: Job) => {
    jobComments.value = job.comment || '';
    selectedJob.value = job;
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

</script>

<template>
    <!-- gcode image viewer modal -->
    <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel"
        aria-hidden="true">
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
                    <div class="mb-3">
                        <label for="newIssue" class="form-label">Enter Issue</label>
                        <input id="newIssue" type="text" placeholder="Enter Issue" v-model="newIssue"
                            class="form-control" required>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="submit" @click.prevent="doCreateIssue" class="btn btn-primary me-2"
                        v-bind:disabled="!newIssue" data-bs-dismiss="modal">Create Issue</button>
                </div>
            </div>
        </div>
    </div>

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
                                <option v-for="issue in issuelist" :key="issue.id" :value="issue">
                                    {{ issue.issue }}
                                </option>
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="submit" @click.prevent="doDeleteIssue" class="btn btn-danger me-2"
                        data-bs-dismiss="modal" :disabled="selectedIssue == undefined">Delete</button>
                </div>
            </div>
        </div>
    </div>

    <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header d-flex align-items-end">
                    <h5 class="modal-title mb-0" id="assignIssueLabel" style="line-height: 1;">Job #{{ selectedJob?.td_id
                        }}</h5>
                    <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px; line-height: 1;">{{
                        selectedJob?.date }}</h6>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
                        @click="selectedIssue = undefined; selectedJob = undefined;"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="">
                        <div class="mb-3">
                            <label for="issue" class="form-label">Select Issue</label>
                            <select name="issue" id="issue" v-model="selectedIssueId" class="form-select" required>
                                <option disabled value="undefined">Select Issue</option>
                                <option v-for="issue in issuelist" :value="issue.id">
                                    {{ issue.issue }}
                                </option>
                                <option disabled class="separator">----------------</option>
                                <option :value=undefined>Unassign Issue</option>
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
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal" @click="doAssignIssue">Save
                        Changes</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <div class="row w-100" style="margin-bottom: 0.5rem;">

            <button v-if="isLoading" class="btn btn-primary w-100" type="button" disabled>
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            </button>
            
            <div class="col-1 text-start" style="padding-left: 0">
                <div style="position: relative;">
                    <button type="button" class="btn btn-primary dropdown-toggle"
                        @click.stop="filterDropdown = !filterDropdown">
                        Filter
                    </button>
                    <form v-show="filterDropdown" class="card dropdown-card p-3 scrollable-filter">
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
                            <div class="card"
                                style="max-height: 120px; overflow-y: auto; background-color: #f4f4f4 !important; border-color: #484848 !important;">
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
                            <div class="card"
                                style="max-height: 120px; overflow-y: auto; background-color: #f4f4f4 !important; border-color: #484848 !important;">
                                <ul class="list-unstyled card-body m-0"
                                    style="padding-top: .5rem; padding-bottom: .5rem;">
                                    <li v-for="issue in issuelist" :key="issue.id">
                                        <div class="form-check">
                                            <input class="form-check-input" type="checkbox" :value="issue.id"
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
                        <label class="form-label ">Date Range:</label>
                        <VueDatePicker class="mb-3" v-model="date" range />
                        <div class="sticky">
                            <div class="mb-2 border-top"
                                style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                            <div class="d-flex justify-content-center">
                                <button @click.prevent="submitFilter" class="btn btn-primary me-3 mb-2">Submit
                                    Filter</button>
                                <button @click.prevent="clearFilter" class="btn btn-danger mb-2">Clear Filter</button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>

            <div class="col-7 text-center"></div>

            <div class="col-4 text-end" style="padding-right: 0">
                <button type="button" class="btn btn-primary me-2" data-bs-toggle="modal"
                    data-bs-target="#assignissueModal">
                    <i class="fas fa-plus"></i>
                    New
                </button>

                <button type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#deleteissueModal">
                    <i class="fas fa-trash-alt"></i>
                    Delete
                </button>
            </div>
        </div>

        <table class="table-striped">
            <thead>
                <tr>
                    <th style="width: 105px;">Ticket ID</th>
                    <th style="width: 150px;">Printer</th>
                    <th style="width: 175px;">Job Title</th>
                    <th style="width: 175px;">File</th>
                    <th style="width: 150px;">Issue</th>
                    <th style="width: 264px">Date errored</th>
                    <th style="width: 200px;">Comment</th>
                    <th style="width: 75px;">Actions</th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td class="truncate" :title="job.td_id.toString()">{{ job.td_id }}</td>
                    <td class="truncate" :title="job.printer_name">{{ job.printer_name }}</td>
                    <td class="truncate" :title="job.name">{{ job.name }}</td>
                    <td class="truncate" :title="job.file_name_original">{{ job.file_name_original }}</td>
                    <td class="truncate" :title="job.error" v-if="job.errorid != null && job.errorid != 0">
                        {{ job.error }}
                    </td>
                    <td v-else>
                    </td>
                    <td>{{job.date}}</td>
                    <td class="truncate" :title="job.comment">{{ job.comment }}</td>
                    <td>
                        <div class="dropdown">
                            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                <button type="button" id="settingsDropdown" data-bs-toggle="dropdown"
                                    aria-expanded="false" style="background: none; border: none;">
                                    <i class="fa-solid fa-bars"></i>
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
                                    <li class="dropdown-submenu position-relative">
                                        <a class="dropdown-item d-flex justify-content-between align-items-center"
                                            @click="handleEmptyRerun">
                                            <div class="d-flex align-items-center">
                                                <i class="fa-solid fa-chevron-left"></i>
                                                <span class="ms-2">Rerun</span>
                                            </div>
                                            <i class="fa-solid fa-arrow-rotate-right"></i>
                                        </a>
                                        <ul class="dropdown-menu dropdown-menu-end">
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
                    <td colspan="8">No jobs with errors found. </td>
                </tr>
            </tbody>
        </table>
        <nav aria-label="Page navigation">
            <ul class="pagination mt-2">
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
.scrollable-filter {
    height: 500px;
    overflow-y: auto;
    overflow-x: hidden;
}

.sticky {
    position: sticky;
    bottom: 0px;
    background: #b9b9b9;
    margin-right: -1rem;
    margin-left: -1rem;
}

.dropdown-card {
    position: absolute !important;
    top: calc(100% + 2px) !important;
    /* Adjust this value to increase or decrease the gap */
    width: 400px;
    z-index: 1000;
    background: #d8d8d8;
    border: 1px solid #484848;
    padding-bottom: 0 !important;
}

.dropdown-submenu {
    position: relative;
    box-sizing: border-box;
}

.dropdown-submenu .dropdown-menu {
    top: -9px;
    right: 100%;
    /* Position the submenu to the left */
    max-height: 200px;
    /* Adjust this value as needed */
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

.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
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
    table-layout: fixed;
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

.form-control {
    background: #f4f4f4;
    border: 1px solid #484848;
}

.form-select {
    background-color: #f4f4f4 !important;
    border-color: #484848 !important;
}
</style>
