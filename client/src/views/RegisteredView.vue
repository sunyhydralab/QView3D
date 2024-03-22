<script setup lang="ts">
import { printers, useGetPorts, useRegisterPrinter, useRetrievePrintersInfo, useHardReset, useQueueRestore, useDeletePrinter, useNullifyJobs, useEditName, useRemoveThread, useEditThread, useDiagnosePrinter, useRepair, type Device, useMoveHead } from '../model/ports'
import { ref, onMounted } from 'vue';
import { toast } from '../model/toast'

const { ports } = useGetPorts();
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
const { move }  = useMoveHead()

let devices = ref<Array<Device>>([]); // Array of all devices -- stores ports for user to select/register
let selectedDevice = ref<Device | null>(null) // device user selects to register.
let customname = ref('') // Stores the user input name of printer 
// let registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system
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

    } catch (error) {
        console.error(error);
    }
});

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
            !printers.value.some(registeredDevice => registeredDevice.device === device.device)
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

    // await removeThread(printer.id)
}

const saveName = async (printer: Device) => {
    await editThread(printer.id, newName.value.trim())
    await editName(printer.id, newName.value.trim())
    printer.name = newName.value.trim();

    editMode.value = false
    newName.value = ''
    editNum.value = undefined // reset editNum
}

const doDiagnose = async (printer: Device) => {
    message.value = `Diagnosing ${printer.name}:<br/><br/>This printer is registered under port ${printer.device}.`
    showMessage.value = true
    let str = await diagnose(printer.device)
    let resstr = str.diagnoseString
    message.value += "<br><br>" + resstr
}

const doRepair = async () => {
    await repair()
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

const doMove = async(printer: Device) => {
    await move(printer.device)
}

</script>
<template>
<div class="modal fade" id="moveModal" tabindex="-1" aria-labelledby="moveModalLabel" aria-hidden="true" data-bs-backdrop="static">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="moveModalLabel">Move Printer Head</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <p>
                    Are you sure you want to move the printer head? Head will move 10mm in the z-direction! Please check printer(s) before!
                </p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-danger" data-bs-dismiss="modal" @click="doMove(selectedDevice!)">Move</button>
            </div>
        </div>
    </div>
</div>

    <div class="container">

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

        <b>Registered View</b>

        <div v-if="printers.length != 0">
            <div class="card" style="width: 18rem;" v-for="printer in printers">
                <div class="card-body">
                    <button
                        @click="openModal('Hard Reset', 'Are you sure you want to do a hard reset of this printer?', 'doHardReset', printer)"
                        data-bs-toggle="modal" data-bs-target="#exampleModal">Hard Reset</button>
                    <button @click="doQueueRestore(printer)">Restore Queue</button>
                    <button
                        @click="openModal('Deregister Printer', 'Are you sure you want to deregister this printer? This will nullify the <strong>printer_id</strong> section in job history.', 'doDelete', printer)"
                        data-bs-toggle="modal" data-bs-target="#exampleModal">Deregister</button>

                    <h6 v-if="!editMode || !(editNum == printer.id)"
                        @click="editMode = true; editNum = printer.id; newName = printer.name || ''"
                        style="cursor: pointer;">
                        Name: {{ printer.name }} (Click
                        to edit)</h6>
                    <div v-else>
                        <input type="text" v-model="newName">
                        <button @click="saveName(printer)">Save</button>
                        <button @click="editMode = false; editNum = undefined; newName = ''">Cancel</button>
                    </div>


                    <h6 class="card-subtitle mb-2 text-body-secondary">{{ printer.device }}</h6>
                    <h6>Description: {{ printer.description }}</h6>
                    <h6>hwid: {{ printer.hwid }}</h6>
                    <h6>Date registered: {{ printer.date }}</h6>

                    <button @click="messageId = printer.id; doDiagnose(printer)">Diagnose Printer</button>
                    <br><br>
                    <div v-if="messageId == printer.id && showMessage == true" style="color:red;">
                        <b v-html="message"></b>
                        <button @click="clearMessage">Clear message</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="form-container">
            <b class="register">REGISTER PRINTERS</b>
            <form methods="POST" @submit.prevent="doRegister">
                <select name="ports" id="ports" v-model="selectedDevice" required>
                    <option disabled value="null">Select Device</option> <!-- Default option -->
                    <option v-for="printer in devices" :value="printer">
                        {{ printer.device }}
                    </option>
                </select>
                <br><br>
                <div v-if="selectedDevice">
                    <b>Device: </b>
                    {{ selectedDevice.device }}
                    <br>
                    <b>Description: </b>
                    {{ selectedDevice.description }}
                    <br>
                    <b>hwid: </b>
                    {{ selectedDevice.hwid }}
                </div>
                <div v-else>
                    No Device Selected
                </div>
                <div v-if="selectedDevice">
                    <label for="name"></label>
                    <input type="text" placeholder="Custom Name" maxlength="49" v-model="customname" required>
                    <br><br>
                    <input type="submit" value="Submit">
                </div>
            </form>
            <div v-if="selectedDevice">
                <br>
                <button data-bs-toggle="modal" data-bs-target="#moveModal">Move Printer Head</button>
            </div>
        </div>
        <button @click="doRepair">Repair Ports</button>
    </div>
</template>

<style scoped>
.form-container {
    border: 2px solid #333;
    padding: 20px;
    margin-top: 20px;
    width: 300px;
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
    margin-bottom: 10px; /* Add margin to the bottom */
}

.card {
    margin-bottom: 20px; /* Add margin to create space between cards */
}

.modal-dialog {
    max-width: 500px; /* Adjust modal width */
}

.modal-content {
    background-color: #fff; /* Change modal background color */
}

.card-body {
    display: flex;
    flex-direction: column;
}

.card-body button {
    margin-bottom: 5px; /* Add margin between buttons */
}

.card-body input[type="text"] {
    margin-bottom: 5px; /* Add margin below input field */
}

.card-body h6 {
    margin-bottom: 5px; /* Add margin below each line */
}

.message {
    color: red;
    margin-top: 10px; /* Add margin to the top */
}


.register {
    color: red;
    margin-bottom: 10px;
    font-size: 1.2em;
}

.register-form {
    margin-top: 10px; /* Add margin to the top of the register form */
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
    box-sizing: border-box; /* Ensure input field width includes padding and border */
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
</style>