<script setup lang="ts">
import { jobTime, useAssignComment, useGetFile, useGetJobFile, useReleaseJob, useRemoveJob, useStartJob, type Job } from '@/model/jobs';
import { printers, useSetStatus, type Device } from '@/model/ports';
import { type Issue, useGetIssues, useAssignIssue } from '../model/issues'
import { useRouter } from 'vue-router';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCode3DLiveViewer from '@/components/GCode3DLiveViewer.vue';
import { onMounted, ref } from 'vue';

const props = defineProps<{
    printer: Device;
}>();

const { setStatus } = useSetStatus();
const { start } = useStartJob()
const { releaseJob } = useReleaseJob()
const { removeJob } = useRemoveJob()
const { getFile } = useGetFile()
const { issues } = useGetIssues()
const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { getFileDownload } = useGetJobFile()

const router = useRouter();
let currentJob = ref<Job>();
let currentPrinter = ref<Device>();
const selectedJob = ref<Job>()
const selectedIssue = ref<Issue>()
let issuelist = ref<Array<Issue>>([])

let isGcodeImageVisible = ref(false)
let isGcodeLiveViewVisible = ref(false)
let jobComments = ref('')

onMounted(async () => {
    const retrieveissues = await issues()
    issuelist.value = retrieveissues
})

const sendToQueueView = (printer: Device | undefined) => {
    if (printer) {
        printer.isQueueExpanded = true;
        router.push({ name: 'QueueViewVue' });
    }
}

const setPrinterStatus = async (printer: Device, status: string) => {
    await setStatus(printer.id, status); // update the status in the backend
    setTimeout(() => {
        // Using setTimeout to ensure the value is reset after the change event is processed
        const selectElement = document.querySelector('select');
        if (selectElement) {
            (selectElement as HTMLSelectElement).value = '';
        }
    });
}

const startPrint = async (printerid: number, jobid: number) => {
    await start(jobid, printerid)
}

const setJob = async (job: Job) => {
    jobComments.value = job.comment || '';
    selectedJob.value = job;
}

const openModal = async (job: Job, printerName: string, num: number, printer: Device) => {
    await jobTime(job, printers)
    currentJob.value = job
    currentJob.value.printer = printerName
    currentPrinter.value = printer
    if (num == 1) {
        isGcodeLiveViewVisible.value = true
    } else if (num == 2) {
        isGcodeImageVisible.value = true
        if (currentJob.value) {
            const file = await getFile(currentJob.value)
            if (file) {
                currentJob.value.file = file
            }
        }
    }
}

const openPrinterInfo = (printer: Device) => {
    printer.isInfoExpanded = !printer.isInfoExpanded;
}

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {
    await releaseJob(jobToFind, key, printerIdToPrintTo)
}

function formatTime(milliseconds: number): string {
    const seconds = Math.floor((milliseconds / 1000) % 60)
    const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
    const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

    const hoursStr = hours < 10 ? '0' + hours : hours
    const minutesStr = minutes < 10 ? '0' + minutes : minutes
    const secondsStr = seconds < 10 ? '0' + seconds : seconds

    if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN')) return '<i>idle</i>'
    return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
    const date = new Date(milliseconds)
    const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })


    if (isNaN(date.getTime()) || timeString === "07:00 PM") {
        return '<i>idle</i>'
    }

    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

const doAssignIssue = async () => {
    if (selectedJob.value === undefined) return
    await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid)

    if (selectedIssue.value !== undefined) {
        await assign(selectedIssue.value.id, selectedJob.value.id)
    }
    await assignComment(selectedJob.value, jobComments.value)
    selectedJob.value.comment = jobComments.value
    selectedIssue.value = undefined
    selectedJob.value = undefined
}

</script>

<template>
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

    <!-- bootstrap 'gcodeLiveViewModal' -->
    <div class="modal fade" id="gcodeLiveViewModal" tabindex="-1" aria-labelledby="gcodeLiveViewModalLaebl"
        aria-hidden="true" @shown.bs.modal="isGcodeLiveViewVisible = true"
        @hidden.bs.modal="isGcodeLiveViewVisible = false">
        <div class="modal-dialog modal-dialog-centered modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="gcodeLiveViewModalLabel">
                        <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <GCode3DLiveViewer v-if="isGcodeLiveViewVisible" :job="currentJob" />
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- bootstrap 'gcodeImageModal' -->
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
                        <GCode3DImageViewer v-if="isGcodeImageVisible" :job="currentJob" />
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- bootstrap 'gcodeModal' -->
    <div class="modal fade" id="gcodeModal" tabindex="-1" aria-labelledby="gcodeModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="gcodeModalLabel"><b>{{ currentJob?.printer }}:</b> {{ currentJob?.name
                        }}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class=" row">
                        <div class="col-sm-12">
                            <div class="card bg-light mb-3">
                                <div class="card-body">
                                    <h5 class="card-title">
                                        <pre> .GCODE VIEWER </pre>
                                    </h5>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>



    <td
        v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
        {{ printer.queue?.[0].id }}
    </td>

    <td v-else><i>idle</i></td>

    <td class="truncate" :title="printer.name">
        <button type="button" class="btn btn-link" @click="sendToQueueView(printer)"
            style="padding: 0; border: none; display: inline-block; width: 100%; text-align: center;">
            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {{ printer.name }}
            </div>
        </button>
    </td>

    <td>
        <div class="d-flex align-items-center justify-content-center">
            <!-- <p class="mb-0 me-2" v-if="printer.status === 'colorchange'" style="color: red">
                Change filament
              </p> -->
            <p v-if="printer.status === 'printing' && printer.queue?.[0]?.released === 0" style="color: #ad6060"
                class="mb-0 me-2">
                Waiting release
            </p>
            <p v-else class="mb-0 me-2">
                {{ printer.status }}
            </p>
        </div>
    </td>

    <td class="truncate" :title="printer.queue?.[0]?.name"
        v-if="(printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange' || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
        {{ printer.queue?.[0]?.name }}
    </td>
    <td v-else></td>

    <td class="truncate" :title="printer.queue?.[0]?.file_name_original"
        v-if="(printer.queue && printer.queue.length > 0 && (printer.status == 'printing' || printer.status == 'complete' || printer.status == 'paused' || printer.status == 'colorchange') || (printer.status == 'offline' && (printer.queue?.[0]?.status == 'complete' || printer.queue?.[0]?.status == 'cancelled')))">
        {{ printer.queue?.[0]?.file_name_original }}
    </td>
    <td v-else></td>

    <td>
        <div class="buttons">

            <button class="btn btn-primary"
                v-if="printer.status == 'configuring' || printer.status == 'offline' || printer.status == 'error'"
                @click="setPrinterStatus(printer, 'ready')">
                Set to Ready
            </button>

            <button class="btn btn-danger"
                v-if="printer.status == 'configuring' || printer.status == 'ready' || printer.status == 'error' || printer.status == 'complete'"
                @click="setPrinterStatus(printer, 'offline')">
                Turn Offline
            </button>

            <button class="btn btn-success" v-if="printer.status == 'printing' && printer.queue?.[0].released == 0"
                @click="startPrint(printer.id!, printer.queue![0].id)">
                Start Print
            </button>

            <button class="btn btn-success" :disabled="Boolean(printer.queue?.[0]?.extruded)"
                @click="setPrinterStatus(printer, 'paused')"
                v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                Pause
            </button>

            <button class="btn btn-success" :disabled="Boolean(printer.queue?.[0]?.extruded)"
                @click="setPrinterStatus(printer, 'colorchange')"
                v-if="(printer.status === 'printing' && printer.queue?.[0]?.released !== 0)">
                Color&nbsp;Change
            </button>

            <button class="btn btn-secondary" @click="setPrinterStatus(printer, 'printing')"
                v-if="printer.status == 'paused'">
                Unpause
            </button>

            <button class="btn btn-danger" @click="setPrinterStatus(printer, 'complete')"
                v-if="(printer.status == 'printing' || printer.status == 'colorchange')">
                Stop
            </button>

            <div v-if="printer.status == 'colorchange'" class="mt-2">
                See LCD screen
            </div>

        </div>
    </td>

    <td style="width: 250px;">
        <div
            v-if="(printer.status === 'printing' || printer.status == 'paused' || printer.status == 'colorchange') && printer.queue && printer.queue![0].released == 1">
            <!-- <div v-for="job in printer.queue" :key="job.id"> -->
            <!-- Display the elapsed time -->
            <div class="progress" style="position: relative;">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar"
                    :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"
                    :aria-valuenow="printer.queue?.[0].progress" aria-valuemin="0" aria-valuemax="100">
                </div>
                <!-- job progress set to 2 decimal places -->
                <p style="position: absolute; width: 100%; text-align: center; color: black;">{{
                    printer.queue?.[0].progress
                        ?
                        `${printer.queue?.[0].progress.toFixed(2)}%` : '0.00%' }}</p>
            </div>
            <!-- </div> -->
        </div>

        <div
            v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'complete' || printer.queue?.[0].status == 'cancelled')">
            <div class="buttons-progress">
                <div type="button" class="btn btn-secondary"
                    @click="releasePrinter(printer.queue?.[0], 1, printer.id!)">
                    Clear
                </div>
                <div class="btn-group">
                    <div class="btn btn-primary no-wrap" @click="releasePrinter(printer.queue?.[0], 2, printer.id!)">
                        Clear/Rerun
                    </div>
                    <div class="btn btn-primary dropdown-toggle dropdown-toggle-split" data-bs-toggle="dropdown"
                        aria-expanded="false">
                    </div>
                    <div class="dropdown-menu">
                        <div class="dropdown-item" v-for="printer in printers" :key="printer.id"
                            @click="releasePrinter(printer.queue?.[0], 2, printer.id!)">
                            {{ printer.name }}
                        </div>
                    </div>
                </div>
                <div type="button" class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#issueModal"
                    @click=setJob(printer.queue!![0])>
                    Fail
                </div>
            </div>
        </div>

        <div
            v-else-if="printer.queue?.[0] && (printer.queue?.[0].status == 'printing' && printer.status == 'complete')">
            <div style="display: flex; justify-content: center; align-items: center;">
                <button class="btn btn-primary w-100" type="button" disabled>
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    <span class="sr-only">Finishing print...</span>
                </button>
            </div>
        </div>
        <div v-else-if="printer.status == 'error'" class="alert alert-danger" role="alert">{{ printer?.error
            }}
        </div>

    </td>

    <td style="width: 1%; white-space: nowrap; height: 55px; padding-top: 5px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <i class="fa" :class="['fa-chevron-down', printer.isInfoExpanded ? 'rotate-up' : 'rotate-down']"
                @click="openPrinterInfo(printer)"></i>
            <div :class="{ 'not-draggable': printer.queue && printer.queue.length == 0 }" class="dropdown">
                <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                    <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                        style="background: none; border: none;">
                        <i class="fa-solid fa-bars"
                            :class="{ 'icon-disabled': printer.queue && printer.queue.length == 0 }"></i>
                    </button>
                    <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                        <li>
                            <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                data-bs-target="#gcodeImageModal" v-if="printer.queue && printer.queue.length > 0"
                                v-bind:job="printer.queue![0]"
                                @click="printer.name && openModal(printer.queue![0], printer.name, 2, printer)">
                                <i class="fa-solid fa-image"></i>
                                <span class="ms-2">GCode Image</span>
                            </a>
                        </li>
                        <li v-if="printer.queue![0]">
                            <a class="dropdown-item d-flex align-items-center"
                                @click="getFileDownload(printer.queue![0].id)"
                                :disabled="printer.queue![0].file_name_original.includes('.gcode:')">
                                <i class="fas fa-download"></i>
                                <span class="ms-2">Download</span>
                            </a>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
    </td>

    <td class="text-center handle" :class="{ 'not-draggable': printers.length <= 1 || printer.isInfoExpanded }"
        :rowspan="printer.isInfoExpanded ? 2 : 1" :style="{ 'vertical-align': printer.isInfoExpanded ? 'middle' : '' }">
        <i class="fas fa-grip-vertical" :class="{ 'icon-disabled': printers.length <= 1 || printer.isInfoExpanded }"></i>
    </td>
</template>

<style scoped>
.border-extended {
    position: relative;
}

.border-extended::after {
    content: "";
    position: absolute;
    right: 0px;
    top: -0.5px;
    bottom: 0;
    width: 1px;
    background: #929292;
    height: calc(100% + 1.5px);
}

.fa {
    transition: transform 0.3s ease-in-out;
}

.rotate-up {
    transform: rotate(0deg);
}

.rotate-down {
    transform: rotate(180deg);
}

.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.buttons {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
}

.buttons>* {
    flex: 1 0 auto;
    margin: 0 0.375rem;
    flex-shrink: 0;
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

.icon-disabled {
    color: #6e7073;
}

.not-draggable {
    pointer-events: none;
}

.sortable-chosen {
    opacity: 0.5;
    background-color: #f2f2f2;
}

.hidden-ghost {
    opacity: 0;
}

.buttons-progress {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.buttons-progress>* {
    margin: 0 0.375rem;
}

.no-wrap {
    white-space: nowrap;
}

table {
    table-layout: fixed;
}

.form-control {
    background: #f4f4f4;
    border: 1px solid #484848;
}

.form-select {
    background-color: #f4f4f4 !important;
    border-color: #484848 !important;
}

.alert {
    margin: 0;
    padding: 0.3rem;
}
</style>