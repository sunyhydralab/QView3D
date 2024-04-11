<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { printers, useRegisterPrinter, useGetPorts, useRetrievePrinters, useRetrievePrintersInfo, useRepair, useMoveHead, type Device } from '../model/ports';
import HoldButton from './HoldButton.vue';
import { toast } from '@/model/toast';

const { ports } = useGetPorts();
const { retrieve } = useRetrievePrinters();
const { retrieveInfo } = useRetrievePrintersInfo();
const { register } = useRegisterPrinter();
const { move } = useMoveHead();

let customname = ref('') // Stores the user input name of printer
let selectedDevice = ref<Device | null>(null)
let devices = ref<Array<Device>>([]) // Stores the list of devices

const emit = defineEmits(['close', 'submit-form'])

onMounted(async () => {
    const allDevices = await ports();  // load all ports
    devices.value = allDevices

    const modalElement = document.getElementById('registerModal')
    if (modalElement) {
        modalElement.addEventListener('hidden.bs.modal', () => {
            emit('close');
        });
    }
})

const doGetPorts = async () => {
  try {
    const allDevices = await ports();
    devices.value = allDevices;

    // toast message
    toast.success('Ports refreshed successfully!');
  } catch (error) {
    // handle error
    toast.error('Failed to refresh ports!');
  }
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
            <div class="modal-content bg-light" style="border: 2px solid #333;">
                <div class="modal-header">
                    <h5 class="modal-title" id="registerModalLabel">Register Printers</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
                        @click="clearSelectedDevice"></button>
                </div>
                <div class="modal-body">
                    <button class="btn btn-primary mb-4 w-100" @click="doGetPorts()">Refresh Ports</button>
                    <form @submit.prevent="$emit('submit-form')">
                        <div class="mb-3">
                            <label for="ports" class="form-label">Select Device</label>
                            <select class="form-select" id="ports" v-model="selectedDevice" required>
                                <option disabled value="null">Select Device</option>
                                <option v-for="printer in devices" :value="printer" :key="printer.device">
                                    {{ printer.device }}
                                </option>
                            </select>
                        </div>
                        <div v-if="selectedDevice">
                            <div class="mb-3">
                                <label class="form-label">Device</label>
                                <p class="form-text border p-1 rounded">{{ selectedDevice.device }}</p>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Description</label>
                                <p class="form-text border p-1 rounded">{{ selectedDevice.description }}</p>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">HWID</label>
                                <p class="form-text border p-1 rounded">{{ selectedDevice.hwid }}</p>
                            </div>
                            <label for="name" class="form-label">Custom Name</label>
                            <input type="text" class="form-control" id="name" placeholder="Custom Name" maxlength="49"
                                v-model="customname" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer d-flex justify-content-between">
                    <button type="submit" class="btn btn-primary" data-bs-dismiss="modal" v-bind:disabled="!customname"
                        @click="doRegister">Submit</button>
                        <div v-if="selectedDevice">
                            <div class="tooltip">
                                <HoldButton :color="'secondary'" @button-held="doMove(selectedDevice)">Move Printer Head</HoldButton>
                                <span class="tooltiptext">Moves printer 10mm upwards! Please check printers before.</span>
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
.tooltip {
    position: relative;
    display: inline-block;
    opacity: 1;
  }
  
  .tooltip .tooltiptext {
    visibility: hidden;
    opacity: 0; /* Add this */
    transition: opacity 0.2s linear, visibility 0.2s linear 0.2s; /* Add delay to visibility transition */
    width: 200px;
    background-color: black;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 5px 0;
    position: absolute;
    z-index: 2000;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
  }
  
  .tooltip .tooltiptext::after {
    content: "";
    position: absolute;
    top: 100%;
    left: 50%;
    margin-left: -5px;
    border-width: 5px;
    border-style: solid;
    border-color: black transparent transparent transparent;
  }
  
  .tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
    transition: opacity 0.2s linear; /* Add this */
  }
</style>