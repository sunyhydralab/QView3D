<script setup lang="ts">
import { onMounted } from 'vue';
import { fabricatorList, retrieveRegisteredFabricators } from '@/models/fabricator'
import PrintModule from '@/components/PrintModule.vue'
onMounted(async () => {
  retrieveRegisteredFabricators()
});
</script>

<template>
  <div class="pt-12">
    <PrintModule v-for="fabricator in fabricatorList" :key="fabricator.id" :fabricator="fabricator" />
  </div>
</template>