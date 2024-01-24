<script setup lang="ts">
// Collect form data 
// const selectedPort = ref<null | string>(null);
// const quantity = ref(1);
// const priority = ref(false)
// const file = ref();
// const fileInput = ref<HTMLInputElement | null>(null)
// const handleFileUpload = async() => {
//     file.value = fileInput.value?.files
// }
</script>
<template>
    <div class="container">
        <p>Submit Job View</p>

        <div class="form-container">
            <form>
                <select required> 
                    <!-- Pull devices from Printer in database -->
                    <option value="None">Device: None</option>
                </select>
                <br><br>
                Upload your .gcode file
                <!-- Decide which file types are compatible with which printer. .gcode v-if printer is compatible with .gcode, .x3g if with .x3g, etc -->
                <input type="file" id="file" name="file" accept=".gcode" required>
                <br><br>

                <!-- Make it so user can't insert negative quantity. Decide on upper limit. -->
                <!-- Make load-balancing feature -->
                <label for="name">Quantity</label>
                <input type="number" id="quantity" name="quantity" required>
                <br><br>

                <label for="priority">Priority job?</label>
                <input type="checkbox" id="priority" name="priority">

                <br><br>
                <!-- This form data does NOT go into the database -- goes into in-memory printer array to be handled. 
                    Also is sent to the QueueView. Perhaps the form is sent to the backend and queueview retrieves that data
                    from the backend. 
                    The job data only gets inserted into the Job table once it is done printing. 
                -->
                <input type="submit" value="Submit">
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