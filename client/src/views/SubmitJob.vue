<script setup lang="ts">
import { printers, useRetrievePrintersInfo, type Device } from '../model/ports'
import { useAddJobToQueue, useGetFile, type Job, useAutoQueue } from '../model/jobs'
import { ref, onMounted, watch, watchEffect, computed } from 'vue'
import { useRoute } from 'vue-router';
import { toast } from '@/model/toast';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue';

const { retrieveInfo } = useRetrievePrintersInfo()
const { addJobToQueue } = useAddJobToQueue()
const { auto } = useAutoQueue()
const { getFile } = useGetFile();

const route = useRoute();

const job = route.params.job ? JSON.parse(route.params.job as string) : null;
const fileName = ref<string>(job ? job.name : '')
const printer = route.params.printer ? JSON.parse(route.params.printer as string) : null;

// Form reference
const form = ref<HTMLFormElement | null>(null);
let isSubmitDisabled = false;

// Collect form data
const selectedPrinters = ref<Array<Device>>([])

const file = ref<File>()
const quantity = ref<number>(1)
const priority = ref<number>(0)
const favorite = ref<boolean>(false)
const name = ref<string>('')
const tdid = ref<number>(0)

const isGcodeImageVisible = ref(false)

// file upload
const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const uploadedFile = target.files ? target.files[0] : undefined;
    if (uploadedFile && uploadedFile.name.length > 50) {
        toast.error('The file name should not be longer than 50 characters');
        target.value = ''
        file.value = undefined
        fileName.value = ''
    } else {
        file.value = uploadedFile
        fileName.value = uploadedFile?.name || ''
    }
}

// validate quantity
const validateQuantity = () => {
    if (quantity.value < 1) {
        quantity.value = 1
    }
    if (quantity.value < selectedPrinters.value.length) {
        toast.error('Quantity must be greater than or equal to the number of selected printers')
        return false;
    }
    return true;
}

// fills printers array with printers that have threads from the database
onMounted(async () => {
    try {
        if (printer) {
            selectedPrinters.value.push(printer)
        }

        if (job) {
            file.value = await getFile(job)
            fileName.value = file.value?.name || ''
            name.value = job.name
        }
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error)
    }
})

const onlyNumber = ($event: KeyboardEvent) => {
    let keyCode = $event.keyCode;
    if ((keyCode < 48 || keyCode > 57) && (keyCode < 96 || keyCode > 105) && keyCode !== 8) { // 48-57 are the keycodes for 0-9, 96-105 are for the numpad 0-9, 8 is for backspace
        $event.preventDefault();
    }
}

// sends job to printer queue
const handleSubmit = async () => {
    let isFavoriteSet = false;
    let res = null
    if (selectedPrinters.value.length == 0) {
        // let numPrints = quantity.value
        // for (let i = 0; i < numPrints; i++) {
        const formData = new FormData() // create FormData object
        formData.append('file', file.value as File) // append form data
        formData.append('name', name.value as string)
        formData.append('priority', priority.value.toString())
        formData.append('td_id', tdid.value.toString())
        // If favorite is true and it's not set yet, set it for the first job only
        if (favorite.value && !isFavoriteSet) {
            formData.append('favorite', 'true')
            isFavoriteSet = true;
        } else {
            formData.append('favorite', 'false')
        }
        try {
            formData.append("quantity", quantity.value.toString())
            res = await auto(formData)
            if (form.value) {
                form.value.reset()
            }
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error)
        }
        // }
        resetValues()
    } else {
        let sub = validateQuantity()
        if (sub == true) {
            let printsPerPrinter = Math.floor(quantity.value / selectedPrinters.value.length) // number of even prints per printer
            let remainder = quantity.value % selectedPrinters.value.length; //remainder to be evenly distributed 
            for (const printer of selectedPrinters.value) {
                let numPrints = printsPerPrinter
                if (remainder > 0) {
                    numPrints += 1
                    remainder -= 1
                }
                // for (let i = 0; i < numPrints; i++) {
                const formData = new FormData() // create FormData object
                formData.append('file', file.value as File) // append form data
                formData.append('name', name.value as string)
                formData.append('printerid', printer?.id?.toString() || '');
                formData.append('priority', priority.value.toString())
                formData.append('quantity', numPrints.toString())
                formData.append('td_id', tdid.value.toString())

                // If favorite is true and it's not set yet, set it for the first job only
                if (favorite.value && !isFavoriteSet) {
                    formData.append('favorite', 'true')
                    isFavoriteSet = true;
                } else {
                    formData.append('favorite', 'false')
                }

                try {
                    res = await addJobToQueue(formData)
                    // reset form
                    if (form.value) {
                        form.value.reset()
                    }
                    // reset Vue refs
                } catch (error) {
                    console.error('There has been a problem with your fetch operation:', error)
                }
                // }
            }
            resetValues()
        }
    }
    if (res.success == true) {
        toast.success('Job added to queue')
    } else if (res.success == false) {
        toast.error('Job failed to add to queue')
    } else {
        toast.error('Failed to add job to queue. Unexpected response.')
    }
}

function resetValues() {
    selectedPrinters.value = [];
    quantity.value = 1;
    priority.value = 0;
    favorite.value = false;
    name.value = "";
    fileName.value = '';
    file.value = undefined;
    tdid.value = 0;
}

watchEffect(() => {
    isSubmitDisabled = !(file.value !== undefined && name.value.trim() !== '' && quantity.value > 0 && (quantity.value >= selectedPrinters.value.length || selectedPrinters.value.length == 0))
});

const openModal = () => {
    isGcodeImageVisible.value = true
}

const allSelected = computed({
    get: () => selectedPrinters.value.length > 0 && selectedPrinters.value.length === printers.value.length,
    set: (value) => {
        if (value) {
            selectedPrinters.value = printers.value.slice();
        } else {
            selectedPrinters.value = [];
        }
    }
});

const triggerFileInput = () => {
    const fileInput = document.getElementById('file') as HTMLInputElement;
    fileInput.click();
}

</script>
<template>
    <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true"
        @shown.bs.modal="isGcodeImageVisible = true" @hidden.bs.modal="isGcodeImageVisible = false">
        <div class="modal-dialog modal-dialog-centered modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="gcodeImageModalLabel">
                        <b>{{ fileName }}</b>
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <GCode3DImageViewer v-if="isGcodeImageVisible" :file="file" />
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <!-- <b>Submit Job View</b> -->

        <div class="card" style="border: 1px solid #484848; background: #d8d8d8;">
            <div class="card-body">
                <form @submit.prevent="handleSubmit" ref="form">

                    <div class="mb-3">
                        <label for="printer" class="form-label">Select Printer</label>
                        <div class="card"
                            style="max-height: 120px; overflow-y: auto; background-color: #f4f4f4 !important; border-color: #484848 !important;">
                            <ul class="list-unstyled card-body m-0" style="padding-top: .5rem; padding-bottom: .5rem;">
                                <li>
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" id="select-all"
                                            v-model="allSelected">
                                        <label class="form-check-label" for="select-all">
                                            Select All
                                        </label>
                                    </div>
                                    <div class="border-top"
                                        style="border-width: 1px; margin-left: -16px; margin-right: -16px;"></div>
                                </li>
                                <li v-for="printer in printers" :key="printer.id">
                                    <div class="form-check">
                                        <input class="form-check-input" type="checkbox" :value="printer"
                                            v-model="selectedPrinters" :id="'printer-' + printer.id">
                                        <label class="form-check-label" :for="'printer-' + printer.id">
                                            {{ printer.name }}
                                        </label>
                                    </div>
                                </li>
                            </ul>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label class="form-label" v-if="selectedPrinters.length === 0">No printer selected, will <b>auto
                                queue</b></label>
                        <label class="form-label" v-else-if="selectedPrinters.length === 1">Selected printer:</label>
                        <label class="form-label" v-else>Selected printers:</label>
                        <ul class="list-group" style="max-height: 200px; overflow-y: auto;">
                            <li v-for="printer in selectedPrinters" class="list-group-item">
                                <b>{{ printer.name }}</b> status: {{ printer.status }}
                            </li>
                        </ul>
                    </div>

                    <div class="mb-3">
                        <label for="file" class="form-label">Upload your .gcode file</label>
                        <input ref="fileInput" @change="handleFileUpload" style="display: none;" type="file" id="file"
                            name="file" accept=".gcode">
                        <div class="input-group">
                            <button type="button" @click="triggerFileInput" class="btn btn-primary">Browse</button>
                            <label class="form-control" style="width: 220px;">
                                <div v-if="fileName" class="ellipsis" style="width: 200px;">
                                    {{ fileName }}
                                </div>
                                <div v-else>No file selected.</div>
                            </label>
                            <button type="button" class="btn btn-primary" data-bs-toggle="modal"
                                data-bs-target="#gcodeImageModal" @click="openModal()" v-bind:disabled="!fileName">
                                <i class="fa-regular fa-image"></i>
                            </button>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="quantity" class="form-label">Quantity</label>
                        <input v-model="quantity" class="form-control" type="number" id="quantity" name="quantity"
                            min="1" @keydown="onlyNumber($event)">
                    </div>

                    <div class="mb-3">
                        <label for="quantity" class="form-label">TeamDynamix ID</label>
                        <input v-model="tdid" class="form-control" type="number" id="tdid" name="tdid"
                            @keydown="onlyNumber($event)">
                    </div>

                    <div class="row mb-3">
                        <div class="col-2">
                            <div class="form-check">
                                <input v-model="priority" class="form-check-input" type="checkbox" id="priority"
                                    name="priority">
                                <label class="form-check-label" for="priority">Priority?</label>
                            </div>
                        </div>

                        <div class="col-6"></div>

                        <div class="col-2">
                            <div class="form-check">
                                <input v-model="favorite" class="form-check-input" type="checkbox" id="favorite"
                                    name="favorite">
                                <label class="form-check-label" for="favorite">Favorite?</label>
                            </div>
                        </div>
                    </div>

                    <div class="mb-3">
                        <label for="name" class="form-label">Name</label>
                        <input v-model="name" class="form-control" type="text" id="name" name="name">
                    </div>

                    <div class="mb-3">
                        <button v-if="selectedPrinters.length > 1" :disabled="isSubmitDisabled" class="btn btn-primary"
                            type="submit">
                            Add to queues
                        </button>
                        <button v-else :disabled="isSubmitDisabled" class="btn btn-primary" type="submit">
                            Add to queue
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<style scoped>
.form-control,
.list-group-item {
    background-color: #f4f4f4 !important;
    border-color: #484848 !important;
}

.form-container {
    border: 2px solid #333;
    padding: 20px;
    width: 300px;
}

.ellipsis {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.card {
    --bs-card-border-color: #484848;
}
</style>