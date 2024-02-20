<script setup lang="ts">
import { useRetrievePrintersInfo, type Device } from '../model/ports'
import { useAddJobToQueue, type Job, useAutoQueue } from '../model/jobs'
import { ref, onMounted } from 'vue'
import { toast } from '@/model/toast';

const { retrieveInfo } = useRetrievePrintersInfo()
const { addJobToQueue } = useAddJobToQueue()
const { auto } = useAutoQueue()

const printers = ref<Array<Device>>([])

// Form reference
const form = ref<HTMLFormElement | null>(null);

// Collect form data
// const selectedPrinter = ref<Device | null>(null)

const selectedPrinters = ref<Array<Device>>([])


const file = ref<File>()
const quantity = ref<number>(1)
const priority = ref<boolean>(false)
const name = ref<string>()

// file upload
const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement
    file.value = target.files ? target.files[0] : undefined
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
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error)
    }
})

// sends job to printer queue
const handleSubmit = async () => {

    if (selectedPrinters.value.length == 0) {
        let numPrints = quantity.value
        for (let i = 0; i < numPrints; i++) {
            const formData = new FormData() // create FormData object
            formData.append('file', file.value as File) // append form data
            formData.append('name', name.value as string)
            try {
                await auto(formData)
                if (form.value) {
                    form.value.reset()
                }
            } catch (error) {
                console.error('There has been a problem with your fetch operation:', error)
            }
        }
        selectedPrinters.value = [];
        quantity.value = 1;
        priority.value = false;
        name.value = undefined;
    }


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
            for (let i = 0; i < numPrints; i++) {
                const formData = new FormData() // create FormData object
                formData.append('file', file.value as File) // append form data
                formData.append('name', name.value as string)
                formData.append('printerid', printer?.id?.toString() || '');
                try {
                    await addJobToQueue(formData)
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
        selectedPrinters.value = [];
        quantity.value = 1;
        priority.value = false;
        name.value = undefined;
    }
}

function appendPrinter(printer: Device) {
    if (!selectedPrinters.value.includes(printer)) {
        selectedPrinters.value.push(printer)
    } else {
        selectedPrinters.value = selectedPrinters.value.filter(p => p !== printer)
    }
}

</script>
<template>
    <div class="container">
        <p>Submit Job View</p>

        <div class="form-container">
            <form @submit.prevent="handleSubmit" ref="form">

                <select required multiple>
                    <option :value="null">Auto Queue</option>
                    <option v-for="printer in printers" :value="printer" :key="printer.id" @click="appendPrinter(printer)">
                        {{ printer.name }}
                    </option>
                </select>

                <div>
                    Selected printer(s): <br>
                    <p v-for="printer in selectedPrinters">
                        <b>{{ printer.name }}</b> status: {{ printer.status }}<br>
                    </p>
                </div>

                <br><br>
                Upload your .gcode file
                <!-- Decide which file types are compatible with which printer. .gcode v-if printer is compatible with .gcode, .x3g if with .x3g, etc -->
                <input @change="handleFileUpload" type="file" id="file" name="file" accept=".gcode" required>
                <br><br>

                <!-- Make it so user can't insert negative quantity. Decide on upper limit. -->
                <!-- Make load-balancing feature -->
                <label for="name">Quantity</label>
                <input v-model="quantity" type="number" id="quantity" name="quantity" min="0" required>
                <br><br>

                <label for="priority">Priority job?</label>
                <input v-model="priority" type="checkbox" id="priority" name="priority">
                <br><br>

                <label for="name">Name</label>
                <input v-model="name" type="text" id="name" name="name" required>

                <br><br>
                <input type="submit" value="Add to queue(s)">
            </form>
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