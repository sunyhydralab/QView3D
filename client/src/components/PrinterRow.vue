<script setup lang="ts">
import { useGetJobFile, useReleaseJob, useStartJob, type Job } from '@/model/jobs';
import { printers, useSetStatus, type Device } from '@/model/ports';
import { useRouter } from 'vue-router';

const props = defineProps<{
    printer: Device;
    openModal: (job: Job, printerName: string, num: number, printer: Device) => Promise<void>;
    setJob: (job: Job) => Promise<void>;
}>();

const { setStatus } = useSetStatus();
const { start } = useStartJob()
const { releaseJob } = useReleaseJob()
const { getFileDownload } = useGetJobFile()

const router = useRouter();

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



const openPrinterInfo = (printer: Device) => {
    printer.isInfoExpanded = !printer.isInfoExpanded;
}

const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {
    await releaseJob(jobToFind, key, printerIdToPrintTo)
}
</script>

<template>
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
                    @click=setJob(printer.queue![0])>
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

    <td style="width: 1%; white-space: nowrap;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <i class="fa fa-chevron-down" :class="printer.isInfoExpanded ? 'rotate-down' : 'rotate-up'"
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
        :rowspan="printer.isInfoExpanded ? 3 : 1" :style="{ 'vertical-align': printer.isInfoExpanded ? 'middle' : '' }">
        <i class="fas fa-grip-vertical"
            :class="{ 'icon-disabled': printers.length <= 1 || printer.isInfoExpanded }"></i>
    </td>
</template>

<style scoped>
@keyframes rotateDown {
    0% {
        transform: rotate(0deg);
    }

    100% {
        transform: rotate(180deg);
    }
}

@keyframes rotateUp {
    0% {
        transform: rotate(180deg);
    }

    100% {
        transform: rotate(0deg);
    }
}

.rotate-down {
    animation: rotateDown 0.3s ease-in-out forwards;
}

.rotate-up {
    animation: rotateUp 0.3s ease-in-out forwards;
}

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

td {
    height: 32px !important;
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