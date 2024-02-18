<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue';

// const { showModal, job, printer } = defineProps(['showModal', 'job', 'printer']);
const emits = defineEmits(['showModal']);
const props = defineProps<{
  job: any,
  printer: any
}>()

const isActive = ref(false);

const toggle = async () => {
  isActive.value = !isActive.value;
};

const closeToggle = async () => {
  isActive.value = false;
}

</script>

<template>
  <button type="button" class="btn btn-danger w-100" @click="toggle">X</button>
  <div class="modal" v-show="isActive">
    <div class="modal-content">
      <span class="close-button" @click="closeToggle">x</span>
      <p>Are you sure you want to delete?</p>
      <button @click="toggle">Yes</button>
      <button @click="closeToggle">No</button>
    </div>
  </div>
</template>

<style scoped>

</style>