<script setup lang="ts">
import { printers } from '@/model/ports';
import draggable from 'vuedraggable'
import PrinterRow from '@/components/PrinterRow.vue'
</script>

<template>
  <div class="container">
    <table class="table-striped" ref="table">
      <tr>
        <th style="width: 64px">Job ID</th>
        <th style="width: 130px">Printer name</th>
        <th style="width: 142px">Printer Status</th>
        <th style="width: 110px">Job Name</th>
        <th style="width: 110px">File</th>
        <th style="width: 314px">Printer Options</th>
        <th style="width: 315px">Progress</th>
        <th style="width: 75px;">Actions</th>
        <th style="width: 58px">Move</th>
      </tr>
      <draggable v-model="printers" tag="tbody" :animation="300" item-key="printer.id" handle=".handle"
        dragClass="hidden-ghost" v-if="printers.length > 0">
        <template #item="{ element: printer }">
          <PrinterRow :printer="printer"></PrinterRow>
        </template>
      </draggable>
    </table>
    <div v-if="printers.length === 0" style="margin-top: 1rem;">
      No printers available. Either register a printer <RouterLink to="/registration">here</RouterLink>, or restart the
      server.
    </div>
  </div>
</template>

<style scoped>
.hidden-ghost {
  opacity: 0;
}

th {
  user-select: none;
}
</style>