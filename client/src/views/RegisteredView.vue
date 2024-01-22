<script setup lang="ts">
import { useGetPorts, type Device } from '../model/ports'
import { ref, onMounted } from 'vue';
const { ports } = useGetPorts();

let devices = ref<Array<Device>>([]);

onMounted(async () => {
    try {
        const devicelist = await ports();
        devices.value = devicelist;
    } catch (error) {
        console.error(error)
    }
})
</script>
<template>
    <div class="container">
        <p>Registered View</p>

        <div class="form-container">
            <form method="POST" action="/botselected">
                <select name="ports" id="ports" required>
                    <option value="None">Device: None</option>
                    <option v-for="printer in devices">
                        {{ printer.device }}
                    </option>
                </select>
                <br><br>
                Upload your .gcode file
                <input type="file" id="file" name="file" accept=".gcode" required>
                <br><br>

                <label for="name">Quantity</label>
                <input type="number" id="quantity" name="quantity" required>
                <br><br>
                <label for="priority">Priority job?</label>
                <input type="checkbox" id="priority" name="priority">

                <br><br>
                <input type="submit" value="Submit">
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