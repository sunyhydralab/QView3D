<script setup lang="ts">
import { api } from '@/model/ports';
import { ref } from 'vue';

const message = ref('')

const registerPrinter = async () => {

    message.value = await api('registeremulator', { 'data': 'wow' });

}

</script>

<template>
    <div>
        <button @click="registerPrinter">Register Emulator</button>
    
        <p v-if="message">Response:{{ message }}</p>
    </div>
</template>

<style scoped>

</style>