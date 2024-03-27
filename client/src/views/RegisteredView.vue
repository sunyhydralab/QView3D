<script setup lang="ts">
import { printers, useGetPorts, useRegisterPrinter, useRetrievePrintersInfo, useHardReset, useQueueRestore, useDeletePrinter, useNullifyJobs, useEditName, useRemoveThread, useEditThread, useDiagnosePrinter, useRepair, type Device, useMoveHead, useRetrievePrinters } from '../model/ports'
import { ref, onMounted } from 'vue';
import { toast } from '../model/toast'

const { ports } = useGetPorts();
const { retrieve } = useRetrievePrinters();
const { retrieveInfo } = useRetrievePrintersInfo();
const { register } = useRegisterPrinter();
const { hardReset } = useHardReset();
const { queueRestore } = useQueueRestore();
const { deletePrinter } = useDeletePrinter();
const { nullifyJobs } = useNullifyJobs();
const { editName } = useEditName();
const { removeThread } = useRemoveThread();
const { editThread } = useEditThread();
const { diagnose } = useDiagnosePrinter();
const { repair } = useRepair()
const { move } = useMoveHead()

let devices = ref<Array<Device>>([]); // Array of all devices -- stores ports for user to select/register
let selectedDevice = ref<Device | null>(null) // device user selects to register.
let customname = ref('') // Stores the user input name of printer 
let registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system
let editMode = ref(false)
let editNum = ref<number | undefined>(0)
let newName = ref('')
let message = ref('')
let showMessage = ref(false)
let messageId = ref<number | undefined>(0)

let modalTitle = ref('');
let modalMessage = ref('');
let modalAction = ref('');
const selectedPrinter = ref<Device | null>(null);

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    try {
        const allDevices = await ports();  // load all ports
        devices.value = allDevices

        const allPrinters = await retrieve(); // load all registered printers
        registered.value = allPrinters
    } catch (error) {
        console.error(error);
    }
});

const doGetPorts = async () => {
    const allDevices = await ports();
    devices.value = allDevices
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
        registered.value = await retrieve();

        // Refresh the devices list
        const allDevices = await ports();
        devices.value = allDevices.filter((device: Device) =>
            !registered.value.some(registeredDevice => registeredDevice.device === device.device)
        );
    }

    // reset values 
    selectedDevice.value = null;
    customname.value = ''
}

const doHardReset = async (printer: Device) => {
    await hardReset(printer.id)
}

const doQueueRestore = async (printer: Device) => {
    await queueRestore(printer.id)
}

const doDelete = async (printer: Device) => {
    printers.value = printers.value.filter(p => p.id !== printer.id)
    await nullifyJobs(printer.id)

    let response = await deletePrinter(printer.id)
    if (response) {
        if (response.success == false) {
            toast.error(response.message)
        } else if (response.success === true) {
            toast.success(response.message)
            await removeThread(printer.id)
        } else {
            console.error('Unexpected response:', response)
            toast.error('Failed to delete printer. Unexpected response.')
        }
    } else {
        console.error('Response is undefined or null')
        toast.error('Failed to delete printer. Unexpected response')
    }

    printers.value = await retrieveInfo();
    registered.value = await retrieve();
    // await removeThread(printer.id)
}

const saveName = async (printer: Device) => {
    await editThread(printer.id, newName.value.trim())
    await editName(printer.id, newName.value.trim())
    printer.name = newName.value.trim();

    printers.value = await retrieveInfo();

    editMode.value = false
    newName.value = ''
    editNum.value = undefined
}

const doDiagnose = async (printer: Device) => {
    message.value = `Diagnosing <b>${printer.name}</b>:<br/><br/>This printer is registered under port <b>${printer.device}</b>.`
    showMessage.value = true
    let str = await diagnose(printer.device)
    let resstr = str.diagnoseString
    message.value += "<br><br>" + resstr
}

const doRepair = async () => {
    await repair()
    clearMessage()
}

const clearMessage = () => {
    showMessage.value = false
    messageId.value = 0
    message.value = ''
}

const openModal = (title: any, message: any, action: any, printer: Device) => {
    modalTitle.value = title;
    modalMessage.value = message;
    modalAction.value = action;
    selectedPrinter.value = printer;
};

const doMove = async (printer: Device) => {
    await move(printer.device)
}

const toggleMessage = (printer: Device) => {
    if (messageId.value == printer.id && showMessage.value) {
        clearMessage()
    } else {
        messageId.value = printer.id
        doDiagnose(printer)
    }
}

</script>
<template>
    <div class="modal fade" id="moveModal" tabindex="-1" aria-labelledby="moveModalLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="moveModalLabel">Move Printer Head</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>
                        Are you sure you want to move the printer head? Head will move 10mm in the z-direction! Please
                        check printer(s) before!
                    </p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-danger" data-bs-dismiss="modal"
                        @click="doMove(selectedDevice!)">Move</button>
                </div>
            </div>
        </div>
    </div>

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
                    <button v-if="modalAction === 'doHardReset'" type="button" class="btn btn-danger"
                        data-bs-dismiss="modal" @click="doHardReset(selectedPrinter!)">Reset</button>
                    <button v-if="modalAction === 'doDelete'" type="button" class="btn btn-danger"
                        data-bs-dismiss="modal" @click="doDelete(selectedPrinter!)">Deregister</button>
                </div>
            </div>
        </div>
    </div>

    <div class="container">
        <b>Registered View</b>

        <div class="form-container bg-light rounded mt-4">
            <h2 class="text-center">Register Printers</h2>
            <div class="d-flex mt-3 mb-3">
                <button class="btn btn-primary me-3" @click="doRepair()">Repair Ports</button>
                <button class="btn btn-primary" @click="doGetPorts()">Refresh Ports</button>
            </div>
            <form @submit.prevent="doRegister">
                <label for="ports" class="form-label">Select Device</label>
                <select class="form-select" id="ports" v-model="selectedDevice" required>
                    <option disabled value="null">Select Device</option>
                    <option v-for="printer in devices" :value="printer" :key="printer.device">
                        {{ printer.device }}
                    </option>
                </select>
                <div v-if="selectedDevice">
                    <div class="mb-3">
                        <label class="form-label">Device</label>
                        <p class="form-text">{{ selectedDevice.device }}</p>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Description</label>
                        <p class="form-text">{{ selectedDevice.description }}</p>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">HWID</label>
                        <p class="form-text">{{ selectedDevice.hwid }}</p>
                    </div>
                    <div class="mb-3">
                        <label for="name" class="form-label">Custom Name</label>
                        <input type="text" class="form-control" placeholder="Custom Name" maxlength="49"
                            v-model="customname" required>
                    </div>
                    <button type="submit" class="btn btn-primary" v-bind:disabled="!customname">Submit</button>
                </div>
            </form>
            <div v-if="selectedDevice" class="mt-3">
                <button class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#moveModal">
                    Move Printer Head
                </button>
            </div>
        </div>

        <div v-if="registered.length != 0" class="row row-cols-1 row-cols-md-3">
            <div class="col" v-for="printer in registered" :key="printer.id">
                <div class="card bg-light rounded" style="width: 385px">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title" v-if="!editMode || !(editNum == printer.id)">{{ printer.name }}</h5>
                            <div v-if="!editMode || !(editNum == printer.id)">
                                <button class="btn btn-primary" style="width: 140px;"
                                    @click="editMode = true; editNum = printer.id; newName = printer.name || ''">
                                    <i class="fas fa-edit"></i> Edit Name
                                </button>
                            </div>
                            <div v-else class="d-flex align-items-center">
                                <input id="editName" type="text" class="form-control me-2" v-model="newName">
                                <button class="btn btn-success me-2" @click="saveName(printer)">Save</button>
                                <button class="btn btn-secondary"
                                    @click="editMode = false; editNum = undefined; newName = ''">Cancel</button>
                            </div>
                        </div>
                        <h6 class="card-text mb-0 text-muted"> <b>Printer device:</b> {{ printer.device }}</h6>
                        <h6 class="card-text mb-0"> <b>Printer description:</b> {{ printer.description }}</h6>
                        <h6 class="card-text mt-0"> <b>Date registered:</b> {{ printer.date }}</h6>
                        <div class="d-flex justify-content-between">
                            <button class="btn btn-danger" data-bs-toggle="modal" data-bs-target="#exampleModal"
                                @click="openModal('Hard Reset', 'Are you sure you want to do a hard reset of this printer?', 'doHardReset', printer)">Hard
                                Reset</button>
                            <button class="btn btn-warning" @click="doQueueRestore(printer)">Restore Queue</button>
                            <button class="btn btn-secondary" data-bs-toggle="modal" data-bs-target="#exampleModal"
                                @click="openModal('Deregister Printer', 'Are you sure you want to deregister this printer? This will nullify the <strong>printer_id</strong> section in job history.', 'doDelete', printer)">Deregister</button>
                        </div>
                        <button class="btn btn-primary" @click="toggleMessage(printer)">
                            {{ messageId == printer.id && showMessage ? 'Clear Message' : 'Diagnose Printer' }}
                        </button>
                        <div v-if="messageId == printer.id && showMessage" class="alert alert-danger">
                            <h6 v-html="message"></h6>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.form-container,
.card {
    border: 2px solid #333;
    margin-top: 20px;
}

.register {
    color: red;
}

.form-container {
    border: 2px solid #333;
    padding: 20px;
    width: 300px;
    margin-top: 20px;
}

.register {
    color: red;
    margin-bottom: 10px;
    /* Add margin to the bottom */
}

.card {
    margin-bottom: 20px;
    /* Add margin to create space between cards */
}

.modal-dialog {
    max-width: 500px;
    /* Adjust modal width */
}

.modal-content {
    background-color: #fff;
    /* Change modal background color */
}

.card-body {
    display: flex;
    flex-direction: column;
}

.card-body button {
    margin-bottom: 5px;
    /* Add margin between buttons */
}

.card-body input[type="text"] {
    margin-bottom: 5px;
    /* Add margin below input field */
}

.card-body h6 {
    margin-bottom: 5px;
    /* Add margin below each line */
}

.message {
    color: red;
    margin-top: 10px;
    /* Add margin to the top */
}


.register {
    color: red;
    margin-bottom: 10px;
    font-size: 1.2em;
}

.register-form {
    margin-top: 10px;
    /* Add margin to the top of the register form */
}

.register-form select {
    margin-bottom: 10px;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 5px;
    width: 100%;
}

.register-form input[type="text"] {
    margin-bottom: 10px;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 5px;
    width: 100%;
    box-sizing: border-box;
    /* Ensure input field width includes padding and border */
}

.register-form input[type="submit"] {
    padding: 10px 16px;
    border: none;
    border-radius: 5px;
    background-color: #007bff;
    color: #fff;
    cursor: pointer;
    width: 100%;
    transition: background-color 0.3s ease;
}

.register-form input[type="submit"]:hover {
    background-color: #0056b3;
}

.alert {
    margin-bottom: 0;
}
</style>