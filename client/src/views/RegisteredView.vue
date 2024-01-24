<script setup lang="ts">
import { useGetPorts, useRegisterPrinter, useRetrievePrinters, type Device } from '../model/ports'
import { ref, onMounted } from 'vue';
const { ports } = useGetPorts();
const { register } = useRegisterPrinter();
const { retrieve } = useRetrievePrinters();

let devices = ref<Array<Device>>([]); // Array of all devices -- stores ports for user to select/register
let selectedDevice = ref<Device | undefined>() // device user selects to register.
let customname = ref('') // Stores the user input name of printer 
let registered = ref<Array<Device>>([]) // Stores array of printers already registered in the system

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    try {
        const devicelist = await ports(); // list of ports to be in form dropdown 
        devices.value = devicelist; // load ports into list 

        const registeredList = await retrieve()//list of previously registered printers 
        registered.value = registeredList; // loads registered printers into registered array 
        console.log(registered.value)

    } catch (error) {
        console.error(error)
    }
})


const doRegister = async () => {
    if (selectedDevice.value && customname.value) {
        selectedDevice.value = {
            device: selectedDevice.value.device,
            description: selectedDevice.value.description,
            hwid: selectedDevice.value.hwid,
            name: customname.value.trim(), // Trim to remove leading and trailing spaces
        };
        // pass RegisteredPrinter data to register function 
        let res = await register(selectedDevice.value)
    }
    // reset values 
    selectedDevice.value = undefined;
    customname.value = ''}
</script>
<template>
    <div class="container">
        <b>Registered View</b>

        <div v-if="registered.length != 0">
            <div class="card" style="width: 18rem;" v-for="printer in registered">
                <div class="card-body">
                    <h6>Name: {{ printer.name }}</h6>
                    <h6 class="card-subtitle mb-2 text-body-secondary">{{ printer.device }}</h6>
                    <h6>Description: {{ printer.description }}</h6>
                    <h6>hwid: {{ printer.hwid }}</h6>
                    <h6>Date registered: {{ printer.date }}</h6>
                </div>
            </div>
        </div>

        <div class="form-container">
            <b class="register">REGISTER PRINTERS</b>
            <form methods="POST" @submit="doRegister">
                <select name="ports" id="ports" v-model="selectedDevice" required>
                    <option :value="null">Select Device</option>
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
        </div>
    </div>
</template>

<style>
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

.register {
    color: red;
}
</style>