<script setup lang="ts">
import type { Device } from '@/model/ports';
import PrinterRow from './PrinterRow.vue';

const props = defineProps<{
    printer: Device;
}>();
const getId = (id: number | undefined) => id ? id.toString() : '';
</script>

<template>
  <div class="table-row" :id="printer.id!.toString()">
    <div class="table-cell">
      <PrinterRow :printer="printer" />
    </div>
    <div class="table-cell" :id="`extra-${printer.id!.toString()}`">
      <td colspan="9">This is an extra row for printer with id: {{ printer.id }}</td>
    </div>
  </div>
</template>

<style scoped>
.table-row {
  display: table-row;
}

.table-cell {
  display: table-cell;
}
</style>