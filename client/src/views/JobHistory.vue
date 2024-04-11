<script setup lang="ts">
import { printers, useRetrievePrintersInfo, type Device } from '../model/ports'
import { pageSize, useGetJobs, type Job, useRerunJob, useGetJobFile, useDeleteJob, useClearSpace, useFavoriteJob, useGetFile, useAssignComment, useUpdateJobStatus } from '../model/jobs';
import { computed, onMounted, onBeforeUnmount, ref } from 'vue';
import { type Issue, useGetIssues, useCreateIssues, useAssignIssue } from '../model/issues'
import { useRouter } from 'vue-router';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'

const { jobhistory, getFavoriteJobs } = useGetJobs()
const { retrieveInfo } = useRetrievePrintersInfo()
const { rerunJob } = useRerunJob()
const { getFileDownload } = useGetJobFile()
const { getFile } = useGetFile()
const { deleteJob } = useDeleteJob()
const { clearSpace } = useClearSpace()
const { favorite } = useFavoriteJob()
const { issues } = useGetIssues()
const { createIssue } = useCreateIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { updateJobStatus } = useUpdateJobStatus()

const selectedPrinters = ref<Array<Number>>([])
const selectedJobs = ref<Array<Job>>([]);
const deleteModalTitle = computed(() => `Deleting ${selectedJobs.value.length} job(s) from database!`);
const clearSpaceTitle = computed(() => 'Clearing space in the database!');
const searchJob = ref(''); // This will hold the current search query
const searchByJobName = ref(true);
const searchByFileName = ref(true);
const selectedJob = ref<Job>()
const newIssue = ref('')
const selectedIssue = ref<Issue | undefined>(undefined)
let issuelist = ref<Array<Issue>>([])

const router = useRouter();

let jobs = ref<Array<Job>>([])
let filter = ref('')
let oldestFirst = ref<boolean>(false)
let order = ref<string>('newest')
let favoriteOnly = ref<boolean>(false)

let currentJob = ref<Job | null>(null);
let isGcodeImageVisible = ref(false);

let page = ref(1)
let totalJobs = ref(0)
let totalPages = ref(1)
let selectAllCheckbox = ref(false);

let modalTitle = ref('');
let modalMessage = ref('');
let modalAction = ref('');
let searchCriteria = ref('');
const isOnlyJobNameChecked = computed(() => searchByJobName.value && !searchByFileName.value);
const isOnlyFileNameChecked = computed(() => !searchByJobName.value && searchByFileName.value);

let buttonTransform = ref(0);
let favoriteJobs = ref<Array<Job>>([])
let jobToUnfavorite: Job | null = null;
let isOffcanvasOpen = ref(false);

let jobComments = ref('')
const showText = ref(false)

let filterDropdown = ref(false)

// computed property that returns the filtered list of jobs. 
let filteredJobs = computed(() => {
    if (filter.value) {
        return jobs.value.filter(job => job.printer.includes(filter.value))
    } else {
        return jobs.value
    }
})

let offcanvasElement: HTMLElement | null = null;

onMounted(async () => {
    try {
        const retrieveissues = await issues()
        issuelist.value = retrieveissues

        offcanvasElement = document.getElementById('offcanvasRight');

        if (offcanvasElement) {
            offcanvasElement.addEventListener('shown.bs.offcanvas', onShownOffcanvas);
            offcanvasElement.addEventListener('hidden.bs.offcanvas', onHiddenOffcanvas);
        }

        const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
        const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds)
        jobs.value = joblist;
        totalJobs.value = total;

        totalPages.value = Math.ceil(total / pageSize.value);
        totalPages.value = Math.max(totalPages.value, 1);

        favoriteJobs.value = await getFavoriteJobs()

        // make 10 dummy printers
        /*
        for (let i = 2; i < 12; i++) {
            printers.value.push({
                id: i, 
                name: `Printer ${i}`,
                device: '',
                description: '',
                hwid: '',
                queue: []
            })
        }
        */

        document.addEventListener('click', closeDropdown);

    } catch (error) {
        console.error(error)
    }
})

const onShownOffcanvas = () => {
    offcanvasElement?.removeAttribute('tabindex');
};

const onHiddenOffcanvas = () => {
    offcanvasElement?.setAttribute('tabindex', '-1');
};

onBeforeUnmount(() => {
    // Cleanup event listeners when component is about to be unmounted
    if (offcanvasElement) {
        offcanvasElement.removeEventListener('shown.bs.offcanvas', onShownOffcanvas);
        offcanvasElement.removeEventListener('hidden.bs.offcanvas', onHiddenOffcanvas);
    }
    document.removeEventListener('click', closeDropdown);
});

const handleRerun = async (job: Job, printer: Device) => {
    await router.push({
        name: 'SubmitJobVue', // the name of the route to SubmitJob.vue
        params: { job: JSON.stringify(job), printer: JSON.stringify(printer) } // the job and printer to fill in the form
    });
}

const handleEmptyRerun = async (job: Job) => {
    await router.push({
        name: 'SubmitJobVue',
        params: { job: JSON.stringify(job) }
    })
}

const changePage = async (newPage: any) => {
    if (newPage < 1 || newPage > Math.ceil(totalJobs.value / pageSize.value)) {
        return;
    }
    selectedJobs.value = [];
    selectAllCheckbox.value = false;

    page.value = newPage
    jobs.value = []
    jobs.value = []
    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];

    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value)
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
    const [, total] = await jobhistory(1, Number.MAX_SAFE_INTEGER, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value);
    totalJobs.value = total;

    totalPages.value = Math.ceil(totalJobs.value / pageSize.value);
    totalPages.value = Math.max(totalPages.value, 1);

    if (page.value > totalPages.value) {
        page.value = totalPages.value;
    }

    // Now fetch the jobs for the current page
    const [joblist] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value);
    jobs.value = joblist;

    selectedJobs.value = [];
    selectAllCheckbox.value = false;
}

function clearFilter() {
    page.value = 1;
    // pageSize.value = 10;

    selectedPrinters.value = [];

    if (order.value === 'oldest') {
        order.value = 'newest';
    }
    favoriteOnly.value = false;

    searchJob.value = '';
    searchByJobName.value = true;
    searchByFileName.value = true;

    submitFilter();
}

const ensureOneCheckboxChecked = () => {
    if (!searchByJobName.value && !searchByFileName.value) {
        searchByJobName.value = true;
    }
}

const confirmDelete = async () => {
    const deletionPromises = selectedJobs.value.map(job => deleteJob(job));
    await Promise.all(deletionPromises);

    const printerIds = selectedPrinters.value.map(p => p).filter(id => id !== undefined) as number[];
    const [joblist, total] = await jobhistory(page.value, pageSize.value, printerIds, oldestFirst.value, searchJob.value, searchCriteria.value, favoriteOnly.value);
    jobs.value = joblist;
    totalJobs.value = total;

    selectedJobs.value = [];
    selectAllCheckbox.value = false;

    submitFilter();

    favoriteJobs.value = await getFavoriteJobs();
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
    submitFilter()
}

const openModal = (title: any, message: any, action: any) => {
    modalTitle.value = title;
    modalMessage.value = message;
    modalAction.value = action;
}

const favoriteJob = async (job: Job, fav: boolean) => {
    await favorite(job, fav);
    favoriteJobs.value = await getFavoriteJobs();

    jobs.value = jobs.value.map(j => {
        if (j.id === job.id) {
            j.favorite = fav;
        }
        return j;
    })

    jobToUnfavorite = null;
}

const toggleButton = () => {
    buttonTransform.value = buttonTransform.value === 0 ? -700 : 0;
    isOffcanvasOpen.value = !isOffcanvasOpen.value;
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

const setJob = async (job: Job) => {
    jobComments.value = job.comment || '';
    selectedJob.value = job;
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
    if (selectedIssue.value !== undefined) {
        await assign(selectedIssue.value.id, selectedJob.value.id)
        selectedJob.value.error = selectedIssue.value!.issue
        await updateJobStatus(selectedJob.value.id, 'error')
        selectedJob.value.status = 'error'

    }
    await assignComment(selectedJob.value, jobComments.value)
    selectedJob.value.comment = jobComments.value
    selectedIssue.value = undefined
    selectedJob.value = undefined
}

const closeDropdown = (evt: any) => {
    if (filterDropdown.value && evt.target.closest('.dropdown-card') === null) {
        filterDropdown.value = false;
    }
}

</script>

<template>
    <!-- error handling modal -->
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
                    <div v-if="selectedIssue !== undefined" class="alert alert-danger mt-3">
                        Warning: Assigning an issue to a job in Job History will set the job status to Error and remove
                        it from any active print queues. Please ensure that the job has been completed before assigning
                        an issue.
                    </div>
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

    <!-- bootstrap off canvas to the right -->
    <div class="offcanvas offcanvas-end" data-bs-backdrop="static" tabindex="-1" id="offcanvasRight"
        aria-labelledby="offcanvasRightLabel" style="background-color: #b9b9b9;">
      <div class="offcanvas-header" style="background-color: #484848; color: #dbdbdb;">
            <div class="container-fluid">
                <div class="row align-items-center">
                    <div class="col">
                        <h5 class="offcanvas-title" id="offcanvasRightLabel">Favorite Prints</h5>
                    </div>
                    <div class="col-auto">
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="offcanvas"
                            aria-label="Close" v-on:click="toggleButton"></button>
                    </div>
                </div>
            </div>
        </div>
        <div class="offcanvas-body" style="max-height: 100vh; overflow-y: auto;">
            <div class="grid-container header">
                <h5>Job Name</h5>
                <h5>File Name</h5>
                <h5>Actions</h5>
            </div>
            <div v-if="favoriteJobs.length > 0" v-for="job in favoriteJobs" :key="job.id" class="mb-3">
                <div class="grid-container job">
                    <p class="my-auto truncate-name">{{ job.name }}</p>
                    <p class="my-auto truncate-file">{{ job.file_name_original }}</p>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-star" style="color: #60AEAE; margin-right: 10px;" data-bs-toggle="modal"
                            data-bs-target="#favoriteModal" @click="jobToUnfavorite = job"></i>
                        <button class="btn btn-secondary download" style="margin-right: 10px;"
                            @click="getFileDownload(job.id)" :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn btn-secondary dropdown-toggle" type="button" id="printerDropdown"
                            data-bs-toggle="dropdown" aria-expanded="false"
                            :disabled="job.file_name_original.includes('.gcode:')">
                            <i class="fa-solid fa-arrow-rotate-right"></i>
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="printerDropdown">
                            <li v-for="printer in printers" :key="printer.id">
                                <a class="dropdown-item" @click="handleRerun(job, printer)"
                                    data-bs-dismiss="offcanvas">{{ printer.name }}</a>
                                <a class="dropdown-item" @click="handleRerun(job, printer)"
                                    data-bs-dismiss="offcanvas">{{ printer.name }}</a>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <p v-else class="text-center text-muted">No favorite jobs found. Favorite your first job!</p>
        </div>
    </div>
    <div class="offcanvas-btn-box" :style="{ transform: `translateX(${buttonTransform}px)` }">
        <button class="btn btn-primary" type="button" data-bs-toggle="offcanvas" data-bs-target="#offcanvasRight"
            aria-controls="offcanvasRight" v-on:click="toggleButton"
            style="border-top-right-radius: 0; border-bottom-right-radius: 0; padding: 5px 10px;">
            <span v-if="isOffcanvasOpen"><i class="fas fa-star"></i></span>
            <span><i class="fas" :class="isOffcanvasOpen ? 'fa-chevron-right' : 'fa-chevron-left'"></i></span>
            <span v-if="!isOffcanvasOpen"><i class="fas fa-star"></i></span>
            <!-- <span v-if="isOffcanvasOpen"><i class="fas fa-star"></i></span>
            <span><i class="fas" :class="isOffcanvasOpen ? 'fa-chevron-right' : 'fa-chevron-left'"></i></span>
            <span v-if="!isOffcanvasOpen"><i class="fas fa-star"></i></span> -->
        </button>
    </div>

    <!-- modal to unfavorite a job in the off canvas -->
    <div class="modal fade" id="favoriteModal" tabindex="-1" aria-labelledby="favoriteModalLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="favoriteModalLabel">Unfavorite Job</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to unfavorite this job?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal"
                        @click="favoriteJob(jobToUnfavorite!, false)">Unfavorite</button>
                </div>
            </div>
        </div>
    </div>

    <!-- modal for delete and clear space -->
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
                    <button v-if="modalAction === 'clear'" type="button" class="btn btn-danger" data-bs-dismiss="modal"
                        @click="clear">Clear Space</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- <b>Job History View</b> -->
        <!-- delete jobs, filter dropdown, clear space -->
        <div class="row w-100" style="margin-bottom: 0.5rem;">

            <div class="col-1 text-start" style="padding-left: 0">
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
                            <input id="pageSize" type="number" v-model.number="pageSize" min="1"
                                class="form-control">
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
                            <input class="form-check-input" type="radio" name="order" id="orderNewest"
                                value="newest" v-model="order">
                            <label class="form-check-label" for="orderNewest">Newest to
                                Oldest</label>
                        </div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="radio" name="order" id="orderOldest"
                                value="oldest" v-model="order">
                            <label class="form-check-label" for="orderOldest">Oldest to Newest</label>
                        </div>
                        <div class="my-2 border-top"
                            style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                        <div class="form-check mb-2">
                            <input class="form-check-input" type="checkbox" name="favorite" id="orderFav"
                                value="favorite" v-model="favoriteOnly">
                            <label class="form-check-label" for="orderFav">Favorites</label>
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

            <div class="col-10 d-flex justify-content-center align-items-center"></div>

            <div class="col-1 text-end" style="padding-right: 0;">
                <button
                    @click="openModal(clearSpaceTitle, 'Are you sure you want to clear space? This action will remove the files from jobs that are older than 6 months, except for those marked as favorite jobs, and this cannot be <b>undone</b>.', 'clear')"
                    class="btn btn-success me-2" data-bs-toggle="modal" data-bs-target="#exampleModal">
                    <i class="fa-solid fa-recycle"></i>
                </button>
            
                <button type="button"
                    @click="openModal(deleteModalTitle, 'Are you sure you want to delete these jobs? This action cannot be <b>undone</b>.', 'confirmDelete')"
                    class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#exampleModal"
                    :disabled="selectedJobs.length === 0">
                    <i class="fas fa-trash-alt"></i>
                </button>
            </div>

        </div>

        <table class="table-striped">
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Printer</th>
                    <th>Job Title</th>
                    <th>File</th>
                    <th>Final Status</th>
                    <th>Date Completed</th>
                    <th>Actions</th>
                    <th class="col-checkbox">
                        <input class="form-check-input" type="checkbox" @change="selectAllJobs" v-model="selectAllCheckbox">
                    </th>
                </tr>
            </thead>
            <tbody v-if="filteredJobs.length > 0">
                <tr v-for="job in filteredJobs" :key="job.id">
                    <td>{{ job.id }}</td>
                    <td>{{ job.printer }}</td>
                    <td>
                        <div style="display: flex; justify-content: start; align-items: center;">
                            <div class="d-flex align-items-center" @click="favoriteJob(job, !job.favorite)">
                                <i :class="job.favorite ? 'fas fa-star' : 'far fa-star'"></i>
                            </div>
                            <div style="margin-left: 10px;">
                                {{ job.name }}
                            </div>
                        </div>
                    </td>
                    <td>{{ job.file_name_original }}</td>
                    <td>{{ job.status }}</td>
                    <td>{{ job.date }}</td>
                    <td>
                        <div class="dropdown">
                            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                <button type="button" id="settingsDropdown" data-bs-toggle="dropdown"
                                    aria-expanded="false" style="background: none; border: none;">
                                    <i class="fas fa-ellipsis"></i>
                                </button>
                                <ul class="dropdown-menu" aria-labelledby="settingsDropdown" style="z-index: 2000;">
                                    <li>
                                        <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                            data-bs-target="#gcodeImageModal" @click="openGCodeModal(job, job.printer)">
                                            <i class="fa-regular fa-image"></i>
                                            <span class="ms-2">Image
                                                Viewer</span>
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
                                            @click="handleEmptyRerun(job)">
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
                    <td>
                        <input class="form-check-input" type="checkbox" v-model="selectedJobs" :value="job">
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

.truncate-name {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.truncate-file {
    max-width: 300px;
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
    padding-left: 10px;
    padding-right: 10px;
    padding-top: 10px;
    border-radius: 5px;
    margin-bottom: 10px;
    background-color: #7561a9;
    color: #dbdbdb;
}

.job {
    padding: 10px;
    border-radius: 5px;
    background-color: #d8d8d8;
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
    border-collapse: collapse;
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