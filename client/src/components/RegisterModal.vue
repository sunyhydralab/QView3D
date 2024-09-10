<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { printers, useRegisterPrinter, useGetPorts, useRetrievePrinters, useRetrievePrintersInfo, useRepair, useMoveHead, type Device } from '../model/ports';
import { toast } from '@/model/toast';

const { ports } = useGetPorts();
const { retrieve } = useRetrievePrinters();
const { retrieveInfo } = useRetrievePrintersInfo();
const { register } = useRegisterPrinter();
const { move } = useMoveHead();

const customname = ref('') // Stores the user input name of printer
const selectedDevice = ref<Device | null>(null)
const devices = ref<Array<Device>>([]) // Stores the list of devices

const emit = defineEmits(['close', 'submit-form'])

onMounted(async () => {
    devices.value = await ports();  // load all ports

    const modalElement = document.getElementById('registerModal')
    if (modalElement) {
        modalElement.addEventListener('shown.bs.modal', () => {
            doGetPorts();
        });

        modalElement.addEventListener('hidden.bs.modal', () => {
            emit('close');
        });
    }
})

const doGetPorts = async () => {
    devices.value = await ports();
}

const doRegister = async () => {
    if (selectedDevice.value && customname.value) {
        selectedDevice.value = {
            device: selectedDevice.value.device,
            description: selectedDevice.value.description,
            hwid: selectedDevice.value.hwid,
            name: customname.value.trim(), // Trim to remove leading and trailing spaces
        };

        await register(selectedDevice.value);

        // Fetch the updated list after registration
        printers.value = await retrieveInfo();

        // Refresh the devices list
        const allDevices = await ports();
        devices.value = allDevices.filter((device: Device) =>
            printers.value ? !printers.value.some(registeredDevice => registeredDevice.device === device.device) : true
        );
    }

    // reset values
    clearSelectedDevice()
}

const clearSelectedDevice = () => {
    setTimeout(() => {
        selectedDevice.value = null;
        customname.value = '';
    }, 500)
}

const doMove = async (printer: Device) => {
    await move(printer.device)
}

</script>

<template>
    <div class="modal fade" id="registerModal" tabindex="-1" aria-labelledby="registerModalLabel" aria-hidden="true"
        data-bs-backdrop="static" data-bs-keyboard="false">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content bg-light">
                <div class="modal-header">
                    <h5 class="modal-title" id="registerModalLabel">Register Printers</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
                        @click="clearSelectedDevice"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="$emit('submit-form')">
                        <div class="mb-3">
                            <label for="ports" class="form-label">Select Device</label>
                            <select class="form-select" id="ports" v-model="selectedDevice" required>
                                <option disabled value="null">Select Device</option>
                                <option v-for="printer in devices" :value="printer" :key="printer.device">
                                    {{ printer.description }}
                                </option>
                            </select>
                        </div>
                        <div v-if="selectedDevice">
                            <div class="mb-3">
                                <label class="form-label">Device</label>
                                <p class="form-text p-1 rounded">{{ selectedDevice.device }}</p>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <p class="form-text p-1 rounded">{{ selectedDevice.description }}</p>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">HWID</label>
                                <p class="form-text p-1 rounded">{{ selectedDevice.hwid }}</p>
                            </div>
                            <label for="name" class="form-label">Custom Name</label>
                            <input type="text" class="form-control" id="name" placeholder="Custom Name" maxlength="49"
                                v-model="customname" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer d-flex justify-content-between">
                    <button type="submit" class="btn btn-primary" data-bs-dismiss="modal" v-bind:disabled="!customname"
                        @click="doRegister">Register</button>
                    <div v-if="selectedDevice">
                        <div class="tooltip">
                            <div type="button" class="btn btn-primary" @click="doMove(selectedDevice as Device)">Home
                                Printer</div>
                            <span class="tooltiptext">This will auto home the selected printer.</span>
                        </div>
                    </div>
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
                        @click="clearSelectedDevice">Close</button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.modal-body {
    background: #b9b9b9;
}

.form-text {
    background: #cdcdcd;
    border: 1px solid #484848;
}

.form-select {
    background-color: #f4f4f4 !important;
    border-color: #484848 !important;
}
</style>