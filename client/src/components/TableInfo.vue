<script setup lang="ts">
import {type Device, printers} from "@/model/ports";
import {jobTime} from "@/model/jobs";

const { printer } = defineProps({
  printer: Object,
});

const getStatusText = (printer: Device) => {
  return printer.status === 'printing' && printer.queue?.[0]?.released === 0 ? 'Waiting release' : printer.status;
};

const printerActions = (printer: Device) => {
  const actions = [];
  if (['configuring', 'offline', 'error'].includes(printer.status)) {
    actions.push({text: 'Set to Ready', class: 'btn btn-primary', method: () => setPrinterStatus(printer, 'ready')});
  }
  if (['configuring', 'ready', 'error', 'complete'].includes(printer.status)) {
    actions.push({text: 'Turn Offline', class: 'btn btn-danger', method: () => setPrinterStatus(printer, 'offline')});
  }
  if (printer.status === 'printing' && printer.queue?.[0].released === 0) {
    actions.push({
      text: 'Start Print',
      class: 'btn btn-secondary',
      method: () => startPrint(printer.id, printer.queue[0].id)
    });
  }
  return actions;
};

// Format time for display
function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60);
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60);
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24);

  return [hours, minutes, seconds]
      .map(unit => (unit < 10 ? '0' + unit : unit))
      .join(':') || '<i>Waiting...</i>';
}

// Format ETA for display
function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds);
  const timeString = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
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
  {text: 'Layer:', style: 'width: 64px; position: relative;'},
  {text: 'Filament', style: 'width: 130px; position: relative;'},
  {text: 'Nozzle:', style: 'width: 142px; position: relative;'},
  {text: 'Bed:', style: 'width: 110px; position: relative;'},
  {text: 'Elapsed:', style: 'width: 110px; position: relative;'},
  {text: 'Remaining:', style: 'width: 314px; position: relative;'},
  {text: 'Total:', style: 'width: 315px; position: relative;'},
  {text: 'ETA:', style: 'width: 75px; position: relative;'},
];
</script>

<template>
  <tr>
    <td>
      {{ printer.queue?.[0]?.td_id || 'idle' }}
    </td>
    <td class="truncate" :title="printer.name">
      {{ printer.name }}
    </td>
    <td>
      {{ getStatusText(printer) }}
    </td>
    <td class="truncate" :title="printer.queue?.[0]?.name">
      {{ printer.queue?.[0]?.name || '' }}
    </td>
    <td class="truncate" :title="printer.queue?.[0]?.file_name_original">
      {{ printer.queue?.[0]?.file_name_original || '' }}
    </td>
    <td>
      <div class="buttons">
        <button v-for="action in printerActions(printer)" :key="action.text" :class="action.class"
                @click="action.method">{{ action.text }}
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

        <!-- Dropdown actions for the printer -->
        <div :class="{ 'not-draggable': printer.queue && printer.queue.length === 0 }" class="dropdown">
          <button type="button" id="settingsDropdown" data-bs-toggle="dropdown" aria-expanded="false"
                  style="background: none; border: none;">
            <i class="fas fa-bars"
               :class="{ 'icon-disabled': printer.queue && printer.queue.length === 0 }"></i>
          </button>
          <ul class="dropdown-menu" aria-labelledby="settingsDropdown">
            <!-- Display GCode Image if the printer has jobs -->
            <li v-if="printer.queue && printer.queue.length > 0">
              <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                 data-bs-target="#gcodeImageModal" v-bind:job="printer.queue[0]"
                 @click="openModal(printer.queue[0], printer.name, 2, printer)">
                <i class="fa-solid fa-image"></i>
                <span class="ms-2">GCode Image</span>
              </a>
            </li>
            <!-- Display GCode Live if the printer has extruded job -->
            <li v-if="printer.queue.length > 0 && printer.queue[0].extruded">
              <a class="dropdown-item d-flex align-items-center" data-bs-toggle="modal"
                 data-bs-target="#gcodeLiveViewModal" v-bind:job="printer.queue[0]"
                 @click="openModal(printer.queue[0], printer.name, 1, printer)">
                <i class="fas fa-code"></i>
                <span class="ms-2">GCode Live</span>
              </a>
            </li>
            <!-- Display Download option -->
            <li v-if="printer.queue.length > 0">
              <a class="dropdown-item d-flex align-items-center"
                 @click="getFileDownload(printer.queue[0].id)">
                <i class="fas fa-download"></i>
                <span class="ms-2">Download</span>
              </a>
            </li>
          </ul>
        </div>
        <!-- Dropdown icon for actions -->
        <i :class="{ 'fa fa-chevron-down': !printer.isInfoExpanded, 'fa fa-chevron-up': printer.isInfoExpanded }"
           @click="openPrinterInfo(printer)">
        </i>

        <div class="text-center handle"><i class="fas fa-grip-vertical"></i></div>
      </div>
    </td>
  </tr>
  <tr v-if="!printer.isInfoExpanded">
    <td v-for="(row, index) in rows" :key="index" :style="row.style" class="borderless-bottom">
      <b>{{ row.text }}</b>
    </td>
  </tr>
  <tr v-if="!printer.isInfoExpanded">
    <td class="borderless-top">
                  <span
                      v-if="printer.queue[0] && printer.queue[0]?.current_layer_height != null && printer.queue[0]?.max_layer_height != null && printer.queue[0]?.max_layer_height !== 0">
                    {{ printer.queue[0]?.current_layer_height + '/' + printer.queue[0]?.max_layer_height }}
                  </span>
      <span v-else>
                    <i>idle</i>
                  </span>
    </td>
    <td class="borderless-top">
      <span v-html="printer.queue[0]?.filament ? printer.queue[0]?.filament : '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer?.extruder_temp ? printer.extruder_temp + '&deg;C' : '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
      <span v-html="printer?.bed_temp ? printer.bed_temp + '&deg;C' : '<i>idle</i>'"></span>
    </td>
    <td class="borderless-top">
                <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.elapsed_time)"></span>
    </td>
    <td class="borderless-top">
                <span v-if="printer.queue[0]?.job_client?.remaining_time !== 0"
                      v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.remaining_time)"></span>
      <span v-else v-html="'00:00:00'"></span></td>
    <td class="borderless-top">
                <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting...' : formatTime(printer.queue[0]?.job_client?.total_time)"></span>
    </td>
    <td class="borderless-top" colspan="2">
                <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting...' : (printer.queue[0]?.extruded ? formatETA(printer.queue[0]?.job_client?.eta) : '<i>Waiting...</i>')"></span>
    </td>
  </tr>
</template>

<style scoped>

</style>