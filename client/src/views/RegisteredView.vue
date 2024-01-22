<script setup lang="ts">
import { useGetPorts, useRegisterPrinter, type Device, type RegisteredDevice } from '../model/ports'
import { ref, onMounted } from 'vue';
const { ports } = useGetPorts();
const { register } = useRegisterPrinter();

// fetch list of connected ports from backend and automatically load them into the form dropdown 
onMounted(async () => {
    try {
        const devicelist = await ports();
        devices.value = devicelist;
    } catch (error) {
        console.error(error)
    }
})

let devices = ref<Array<Device>>([]); // Array of type Device  
let selectedDevice = ref<Device | undefined>()
let name = ref('')

let registeredPrinter = ref<RegisteredDevice | undefined>()

const doRegister = async () => {
    if (selectedDevice.value && name.value) {
        registeredPrinter.value = {
            device: selectedDevice.value.device,
            description: selectedDevice.value.description,
            hwid: selectedDevice.value.hwid,
            customname: name.value.trim(), // Trim to remove leading and trailing spaces
        };
        // pass RegisteredPrinter data to register function 
        let res = await register(registeredPrinter.value)
        console.log(res)
    }
    // reset values 
    selectedDevice.value = undefined;
    name.value = ''
    console.log(registeredPrinter.value);
}
</script>
<template>
    <div class="container">
        <p>Registered View</p>

        <div class="form-container">
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
                    <input type="text" placeholder="Custom Name" maxlength="49" v-model="name" required>
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
</style>