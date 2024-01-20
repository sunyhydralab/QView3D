<template>
    <button type="button" class="btn btn-primary">{{ msg }}</button>
</template>

<script setup lang="ts">
import axios from 'axios'
import { ref, onMounted } from 'vue'

const msg = ref("");

const getResponse = async () => {
  try {
    const response = await axios.get('http://localhost:8000/shark', { withCredentials: true });
    msg.value = response.data;
  } catch (error) {
    console.error('Error:', error);
  }
};

onMounted(() => {
  getResponse();
});
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
</style>