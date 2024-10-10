<script setup lang="ts">
import { type Device, printers } from "@/model/ports";
import { jobTime } from "@/model/jobs";

// Define the props and ensure proper type checking
const props = defineProps<{
  printer: Device;
}>();

const getStatusText = (printer: Device) => {
  return printer.status === 'printing' && printer.queue?.[0]?.released === 0 ? 'Waiting release' : printer.status || 'Unknown';
};

const printerActions = (printer: Device) => {
  const actions = [];
  if (['configuring', 'offline', 'error'].includes(printer.status)) {
    actions.push({ text: 'Set to Ready', class: 'btn btn-primary', method: () => setPrinterStatus(printer, 'ready') });
  }
  if (['configuring', 'ready', 'error', 'complete'].includes(printer.status)) {
    actions.push({ text: 'Turn Offline', class: 'btn btn-danger', method: () => setPrinterStatus(printer, 'offline') });
  }
  if (printer.status === 'printing' && printer.queue?.[0]?.released === 0) {
    actions.push({
      text: 'Start Print',
      class: 'btn btn-secondary',
      method: () => startPrint(printer.id, printer.queue[0].id),
    });
  }
  return actions;
};

// Format time for display
function formatTime(milliseconds: number | null | undefined): string {
  if (!milliseconds || isNaN(milliseconds)) return '<i>Waiting...</i>';
  const seconds = Math.floor((milliseconds / 1000) % 60);
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60);
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24);
  return [hours, minutes, seconds]
      .map(unit => (unit < 10 ? '0' + unit : unit))
      .join(':');
}

// Format ETA for display
function formatETA(milliseconds: number | null | undefined): string {
  const date = new Date(milliseconds || 0);
  const timeString = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
  return !isNaN(date.getTime()) && timeString !== '07:00 PM' ? timeString : '<i>Waiting...</i>';
}

const openPrinterInfo = async (printer: Device) => {
  if (printer.queue && printer.queue[0]) {
    await jobTime(printer.queue[0], printers);
  }
  printer.isInfoExpanded = !printer.isInfoExpanded;
};

const rows = [
  { text: 'Layer:', style: 'width: 64px; position: relative;' },
  { text: 'Filament', style: 'width: 130px; position: relative;' },
  { text: 'Nozzle:', style: 'width: 142px; position: relative;' },
  { text: 'Bed:', style: 'width: 110px; position: relative;' },
  { text: 'Elapsed:', style: 'width: 110px; position: relative;' },
  { text: 'Remaining:', style: 'width: 314px; position: relative;' },
  { text: 'Total:', style: 'width: 315px; position: relative;' },
  { text: 'ETA:', style: 'width: 75px; position: relative;' },
];
</script>

<template>
  <tr>
    <td>{{ printer.queue?.[0]?.td_id || 'idle' }}</td>
    <td class="truncate" :title="printer.name">
      {{ printer.name || 'Unnamed Printer' }}
    </td>
    <td>{{ getStatusText(printer) }}</td>
    <td class="truncate" :title="printer.queue?.[0]?.name">
      {{ printer.queue?.[0]?.name || 'No Job' }}
    </td>
    <td class="truncate" :title="printer.queue?.[0]?.file_name_original">
      {{ printer.queue?.[0]?.file_name_original || 'No File' }}
    </td>
    <td>
      <div class="buttons">
        <button
            v-for="action in printerActions(printer)"
            :key="action.text"
            :class="action.class"
            @click="action.method"
        >
          {{ action.text }}
        </button>
      </div>
    </td>
    <td>
      <div class="progress-wrapper">
        <div v-if="printer.queue?.[0]?.progress !== undefined" class="progress">
          <div class="progress-bar" :style="{ width: (printer.queue?.[0].progress || 0) + '%' }"></div>
          <p class="progress-text">{{ printer.queue?.[0]?.progress?.toFixed(2) + '%' || '0.00%' }}</p>
        </div>
      </div>
    </td>
    <td style="width: 1%; white-space: nowrap;">
      <div style="display: flex; justify-content: center; align-items: center;">
        <div class="dropdown" :class="{ 'not-draggable': printer.queue && printer.queue.length === 0 }">
          <button
              type="button"
              id="settingsDropdown"
              data-bs-toggle="dropdown"
              aria-expanded="false"
              style="background: none; border: none;"
          >
            <i class="fas fa-bars" :class="{ 'icon-disabled': printer.queue && printer.queue.length === 0 }"></i>
          </button>
          <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
            <li v-if="printer.queue && printer.queue.length > 0">
              <a
                  class="dropdown-item d-flex align-items-center"
                  data-bs-toggle="modal"
                  data-bs-target="#gcodeImageModal"
                  @click="openModal(printer.queue[0], printer.name, 2, printer)"
              >
                <i class="fa-solid fa-image"></i>
                <span class="ms-2">GCode Image</span>
              </a>
            </li>
            <li v-if="printer.queue.length > 0 && printer.queue[0].extruded">
              <a
                  class="dropdown-item d-flex align-items-center"
                  data-bs-toggle="modal"
                  data-bs-target="#gcodeLiveViewModal"
                  @click="openModal(printer.queue[0], printer.name, 1, printer)"
              >
                <i class="fas fa-code"></i>
                <span class="ms-2">GCode Live</span>
              </a>
            </li>
            <li v-if="printer.queue.length > 0">
              <a
                  class="dropdown-item d-flex align-items-center"
                  @click="getFileDownload(printer.queue[0].id)"
              >
                <i class="fas fa-download"></i>
                <span class="ms-2">Download</span>
              </a>
            </li>
          </ul>
        </div>
        <i
            :class="{
            'fa fa-chevron-down': !printer.isInfoExpanded,
            'fa fa-chevron-up': printer.isInfoExpanded,
          }"
            @click="openPrinterInfo(printer)"
        ></i>
        <div class="text-center handle">
          <i class="fas fa-grip-vertical"></i>
        </div>
      </div>
    </td>
  </tr>
  <tr v-if="printer.isInfoExpanded">
    <td v-for="(row, index) in rows" :key="index" :style="row.style" class="borderless-bottom">
      <b>{{ row.text }}</b>
    </td>
  </tr>
  <tr v-if="printer.isInfoExpanded">
    <td class="borderless-top">
      <span v-if="printer.queue[0]?.current_layer_height && printer.queue[0]?.max_layer_height">
        {{ printer.queue[0].current_layer_height }} / {{ printer.queue[0].max_layer_height }}
      </span>
      <span v-else><i>idle</i></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.queue[0]?.filament || '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.extruder_temp ? `${printer.extruder_temp}°C` : '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.bed_temp ? `${printer.bed_temp}°C` : '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.elapsed_time)"></span>
    </td>
    <td class="borderless-top">
      <span v-if="printer.queue[0]?.job_client?.remaining_time"
            v-html="formatTime(printer.queue[0]?.job_client?.remaining_time)"></span>
      <span v-else><i>00:00:00</i></span>
    </td>
    <td class="borderless-top">
      <span v-html="formatTime(printer.queue[0]?.job_client?.total_time)"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.queue[0]?.extruded ? formatETA(printer.queue[0]?.job_client?.eta) : '<i>Waiting...</i>'"></span>
    </td>
  </tr>
</template>

<style scoped>
/* Custom styles for the table and actions */
.progress-wrapper {
  position: relative;
}

.progress-bar {
  width: 100%;
  height: 100%;
}

.progress-text {
  position: absolute;
  width: 100%;
  text-align: center;
  color: var(--color-background-font);
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.borderless-top {
  border-top: none;
}

.borderless-bottom {
  border-bottom: none;
}
</style>
