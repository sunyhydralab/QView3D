<script setup lang="ts">
  import { ref, onMounted } from 'vue'
  import { useRetrievePrintersInfo, type Device } from '../model/ports'
  const { retrieveInfo } = useRetrievePrintersInfo()

  const printers = ref<Array<Device>>([]) // Get list of open printer threads 


  onMounted(async () => {
    try {
        printers.value = await retrieveInfo()
    } catch (error) {
        console.error('There has been a problem with your fetch operation:', error)
    }
})


</script>
<template>
  <div class="container">
    <p>Queue View</p>
    <!-- Get list of printers and their queue attribute. Queue has job objects.  -->

  </div>
</template>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>