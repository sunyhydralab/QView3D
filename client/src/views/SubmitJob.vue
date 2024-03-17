<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useAddJobToQueue, useGetFile, type Job, useAutoQueue } from '../model/jobs'
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router';
import { toast } from '@/model/toast';

const { retrieveInfo } = useRetrievePrintersInfo()
const { addJobToQueue } = useAddJobToQueue()
const { auto } = useAutoQueue()
const { getFile } = useGetFile();

const route = useRoute();
const printers = ref<Array<Device>>([])

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
const name = ref<string>()

// file upload
const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement;
    const uploadedFile = target.files ? target.files[0] : undefined;
    if (uploadedFile && uploadedFile.name.length > 50) {
        toast.error('The file name should not be longer than 50 characters');
        target.value = ''
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
        printers.value = await retrieveInfo()

        if (printer) {
            appendPrinter(printer)
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
    if ((keyCode < 48 || keyCode > 57) && keyCode !== 8) { // 48-57 are the keycodes for 0-9, 8 is for backspace
        $event.preventDefault();
    }
}

// sends job to printer queue
const handleSubmit = async () => {
    let isFavoriteSet = false;

    if (selectedPrinters.value.length == 0) {
        let numPrints = quantity.value
        for (let i = 0; i < numPrints; i++) {
            const formData = new FormData() // create FormData object
            formData.append('file', file.value as File) // append form data
            formData.append('name', name.value as string)
            formData.append('priority', priority.value.toString())

            // If favorite is true and it's not set yet, set it for the first job only
            if (favorite.value && !isFavoriteSet) {
                formData.append('favorite', 'true')
                isFavoriteSet = true;
            } else {
                formData.append('favorite', 'false')
            }

            try {
                await auto(formData)
                if (form.value) {
                    form.value.reset()
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error)
            }
        }
        resetValues()
    } else {
        let sub = validateQuantity()
        let res = null
        if (sub == true) {
            if (selectedPrinters.value.length == 0) {
                let numPrints = quantity.value
                for (let i = 0; i < numPrints; i++) {
                    const formData = new FormData() // create FormData object
                    formData.append('file', file.value as File) // append form data
                    formData.append('name', name.value as string)
                    formData.append('priority', priority.value.toString())

                    // If favorite is true and it's not set yet, set it for the first job only
                    if (favorite.value && !isFavoriteSet) {
                        formData.append('favorite', 'true')
                        isFavoriteSet = true;
                    } else {
                        formData.append('favorite', 'false')
                    }

                    try {
                        res = await auto(formData)
                        if (form.value) {
                            form.value.reset()
                        }
                    } catch (error) {
                        console.error('There has been a problem with your fetch operation:', error)
                    }
                }
                resetValues()
            }
            else {
                console.log(selectedPrinters.value)
                let printsPerPrinter = Math.floor(quantity.value / selectedPrinters.value.length) // number of even prints per printer
                let remainder = quantity.value % selectedPrinters.value.length; //remainder to be evenly distributed 
                for (const printer of selectedPrinters.value) {
                    let numPrints = printsPerPrinter
                    if (remainder > 0) {
                        numPrints += 1
                        remainder -= 1
                    }
                    for (let i = 0; i < numPrints; i++) {
                        const formData = new FormData() // create FormData object
                        formData.append('file', file.value as File) // append form data
                        formData.append('name', name.value as string)
                        formData.append('printerid', printer?.id?.toString() || '');
                        formData.append('priority', priority.value.toString())

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
                    }
                }
                resetValues()
            }
        }
        if (res.success == true) {
            toast.success('Job added to queue')
        } else {
            toast.error('Job failed to add to queue')
        }

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
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.some(p => p.id === printer.id)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p.id !== printer.id)
    }
}

watch([file, name, quantity, selectedPrinters], () => {
    isSubmitDisabled = !file.value || !name.value || !quantity.value || selectedPrinters.value.length === 0;
});

</script>
<template>
    <div class="container py-5">
        <h2 class="mb-4">Submit Job View</h2>

        <div class="card">
            <div class="card-body">
                <form @submit.prevent="handleSubmit" ref="form">

                    <div class="mb-3">
                        <label for="printer" class="form-label">Select Printer</label>
                        <select id="printer" class="form-select" multiple>
                            <option :value="null">Auto Queue</option>
                            <option v-for="printer in printers" :value="printer" :key="printer.id"
                                @click="appendPrinter(printer)">
                                {{ printer.name }}
                            </option>
                        </select>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Selected printer(s):</label>
                        <ul class="list-group">
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
                            <button type="button" @click="($refs.fileInput as HTMLInputElement).click()"
                                class="btn btn-primary">Browse</button> <label class="form-control">
                                <span v-if="fileName">{{ fileName }}</span>
                                <span v-else>No file selected.</span>
                            </label>
                        </div>
                    </div>

                    <div class="row mb-3">
                        <div class="col">
                            <label for="quantity" class="form-label">Quantity</label>
                            <input v-model="quantity" class="form-control" type="number" id="quantity" name="quantity"
                                min="1" @keydown="onlyNumber($event)">
                        </div>

                        <div class="col">
                            <div class="form-check mt-4">
                                <input v-model="priority" class="form-check-input" type="checkbox" id="priority"
                                    name="priority">
                                <label class="form-check-label" for="priority">Priority?</label>
                            </div>
                            <div class="form-check mt-2">
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
.container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.form-container {
    border: 2px solid #333;
    padding: 20px;
    margin-top: 20px;
    width: 300px;
}
</style>