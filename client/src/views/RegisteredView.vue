<script setup lang="ts">
import { printers, useGetPorts, useRetrievePrintersInfo, useHardReset, useDeletePrinter, useNullifyJobs, useEditName, useRemoveThread, useEditThread, useDiagnosePrinter, useRepair, type Device, useRetrievePrinters, useMoveHead } from '../model/ports'
import { isLoading } from '../model/jobs'
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue';
import { toast } from '../model/toast'
import RegisterModal from '../components/RegisterModal.vue'
import router from '@/router';

const { retrieve } = useRetrievePrinters();
const { retrieveInfo } = useRetrievePrintersInfo();
const { hardReset } = useHardReset();
const { deletePrinter } = useDeletePrinter();
const { nullifyJobs } = useNullifyJobs();
const { editName } = useEditName();
const { removeThread } = useRemoveThread();
const { editThread } = useEditThread();
const { diagnose } = useDiagnosePrinter();
const { repair } = useRepair();
const { move } = useMoveHead();

const registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system
const editMode = ref(false)
const editNum = ref<number | undefined>(0)
const newName = ref('')
const message = ref('')
const showMessage = ref(false)
const messageId = ref<number | undefined>(0)

const modalTitle = ref('');
const modalMessage = ref('');
const modalAction = ref('');
const selectedPrinter = ref<Device | null>(null);

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    isLoading.value = true
    const allPrinters = await retrieve(); // load all registered printers
    registered.value = allPrinters
    isLoading.value = false
});

const doHardReset = async (printer: Device) => {
    isLoading.value = true
    await hardReset(printer.id).then(() => {
        router.go(0)
    }).catch(() => {
        toast.error('Failed to reset printer')
    })
    isLoading.value = false
}

const doDelete = async (printer: Device) => {
    isLoading.value = true
    if (printer.status == "printing") {
        toast.error("Cannot deregister printer while status is printing. Please wait for the printer to finish")
    }
    const printerId = printer.id;
    const foundPrinter = printers.value.find(p => p.id === printerId);    // code to find printer where printer.id is equal to the printer.id in the printers array

    if (foundPrinter?.status === "printing") {
        toast.error("Cannot deregister printer while status is printing. Please turn offline or wait for the printer to finish printing.")
        return
    }

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
    isLoading.value = false
    // await removeThread(printer.id)
}

const saveName = async (printer: Device) => {
    isLoading.value = true
    await editThread(printer.id, newName.value.trim())
    await editName(printer.id, newName.value.trim())
    printer.name = newName.value.trim();

    printers.value = await retrieveInfo();
    isLoading.value = false

    editMode.value = false
    newName.value = ''
    editNum.value = undefined
}

const doRepair = async () => {
    isLoading.value = true
    await repair().then(() => {
        router.go(0)
    }).catch(() => {
        toast.error('Failed to repair ports')
    })
    isLoading.value = false
}

const doMove = async (printer: Device) => {
    isLoading.value = true
    await move(printer.device).then(() => {
        toast.success('Printer moved to home position')
    }).catch(() => {
        toast.error('Failed to move printer to home position')
    })
    isLoading.value = false
}

const doDiagnose = async (printer: Device) => {
    isLoading.value = true
    message.value = `Diagnosing <b>${printer.name}</b>:<br/><br/>This printer is registered under port <b>${printer.device}</b>.`
    showMessage.value = true
    let str = await diagnose(printer.device)
    let resstr = str.diagnoseString
    message.value += "<br><br>" + resstr
    isLoading.value = false
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

const toggleMessage = (printer: Device) => {
    if (messageId.value == printer.id && showMessage.value) {
        clearMessage()
    } else {
        messageId.value = printer.id
        doDiagnose(printer)
    }
}

const doCloseRegisterModal = async () => {
    registered.value = await retrieve();
}

</script>
<template>
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
        <button type="button" class="btn btn-primary mb-2" data-bs-toggle="modal" data-bs-target="#registerModal">
            Register Printer
        </button>
        <RegisterModal id="registerModal" @close="doCloseRegisterModal" />

        <div v-if="registered.length != 0" class="d-flex flex-wrap justify-content-start">
            <div v-for="printer in registered" :key="printer.id">
                <div class="card m-2 rounded" style="width: 416px; background: #d8d8d8;">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center">
                            <h5 class="card-title mb-4" v-if="!editMode || !(editNum == printer.id)">{{ printer.name }}
                            </h5>
                            <div class="dropdown" v-if="!editMode || !(editNum == printer.id)">
                                <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                                    <button type="button" id="settingsDropdown" data-bs-toggle="dropdown"
                                        aria-expanded="false" style="color: var(--color-background-font); background: transparent; border: none;">
                                        <i class="fa-solid fa-bars"></i>
                                    </button>
                                    <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
                                        <li>
                                            <a class="dropdown-item d-flex align-items-center"
                                                @click="editMode = true; editNum = printer.id; newName = printer.name || ''">
                                                <i class="fas fa-edit"></i>
                                                <span class="ms-2">Edit Name</span>
                                            </a>
                                        </li>
                                        <div class="tooltip" style="width: 100%;">
                                            <li>
                                                <a class="dropdown-item d-flex align-items-center"
                                                    style="font-size: 1rem;" data-bs-toggle="modal"
                                                    data-bs-target="#exampleModal"
                                                    @click="openModal('Hard Reset', 'Are you sure you want to do a hard reset of this printer?', 'doHardReset', printer)">
                                                    <i class="fas fa-sync"></i>
                                                    <span class="ms-2">Hard Reset</span>
                                                </a>
                                            </li>
                                            <span class="tooltiptext">This wipes the queue and resets the printer's
                                                communication thread.</span>
                                        </div>
                                        <li>
                                            <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                                                data-bs-target="#exampleModal"
                                                @click="openModal('Deregister Printer', 'Are you sure you want to deregister this printer? This will nullify the <strong>printer_id</strong> section in job history.', 'doDelete', printer)">
                                                <i class="fas fa-trash"></i>
                                                <span class="ms-2">Deregister</span>
                                            </a>
                                        </li>
                                        <li>
                                            <a class="dropdown-item d-flex align-items-center"
                                                @click="toggleMessage(printer)">
                                                <i class="fas fa-stethoscope"></i>
                                                <span class="ms-2">{{ messageId == printer.id && showMessage ? 'Clear Message' : 'Diagnose Printer' }}</span>
                                            </a>
                                        </li>
                                        <li>
                                            <a class="dropdown-item d-flex align-items-center" @click="doMove(printer)">
                                                <i class="fas fa-home"></i>
                                                <span class="ms-2">Home Printer</span>
                                            </a>
                                        </li>
                                    </ul>
                                </div>
                            </div>
                            <div v-if="editMode && (editNum == printer.id)" class="d-flex align-items-center"
                                style="margin-bottom: 5px;">
                                <input id="editName" type="text" class="form-control me-2" v-model="newName">
                                <button class="btn btn-success me-2" @click="saveName(printer)">Save</button>
                                <button class="btn btn-secondary"
                                    @click="editMode = false; editNum = undefined; newName = ''">Cancel</button>
                            </div>
                        </div>
                        <h6 class="card-text mb-0"> <b>Printer device:</b> {{ printer.device }}</h6>
                        <h6 class="card-text mb-0"> <b>Printer description:</b> {{ printer.description }}</h6>
                        <h6 class="card-text mb-0"> <b>Date registered:</b> {{ printer.date }}</h6>
                        <h6 class="card-text mt-0"> <b>HWID:</b> {{ printer.hwid }}</h6>

                        <div v-if="messageId == printer.id && showMessage"
                            class="alert alert-danger d-flex flex-column align-items-center justify-content-center">
                            <h6 v-html="message"></h6>
                            <div class="d-flex justify-content-between">
                                <button class="btn btn-secondary me-3" @click="clearMessage()">Clear</button>
                                <button class="btn btn-primary w-100" @click="doRepair()">Repair Ports</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.dropdown {
    background-color: var(--color-background-mute);
    color: var(--color-background-font)
}
.dropdown-item {
    background-color: var(--color-background);
    color: var(--color-background-font);
    display: flex;
    align-items: center;
    padding-left: .5rem;
}
.dropdown-item:hover {
    background-color: var(--color-background-mute);
}

.dropdown-item i {
    width: 20px;
}

.dropdown-item span {
    margin-left: 10px;
}

.card {
    background-color: var(--color-background);
    border: 1px solid var(--color-border);
}

.modal-dialog {
    max-width: 500px;
    /* Adjust modal width */
}

.card-body {
    color: var(--color-background-font);
    background-color: var(--color-background-mute);
    border: 0 solid var(--color-border-hover);
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

.register-form select {
    margin-bottom: 10px;
    padding: 8px;
    border: 1px solid var(--color-background);
    border-radius: 5px;
    width: 100%;
}

.register-form input[type="text"] {
    margin-bottom: 10px;
    padding: 8px;
    border: 1px solid var(--color-background);
    border-radius: 5px;
    width: 100%;
    box-sizing: border-box;
    /* Ensure input field width includes padding and border */
}

.register-form input[type="submit"] {
    padding: 10px 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    width: 100%;
    transition: background-color 0.3s ease;
}

.alert {
    margin-bottom: 0;
}
</style>