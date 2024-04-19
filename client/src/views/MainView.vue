<script setup lang="ts">
import { ref } from 'vue';
import { printers } from '@/model/ports';
import draggable from 'vuedraggable'
import PrinterRow from '@/components/PrinterRow.vue'


function formatTime(milliseconds: number): string {
  const seconds = Math.floor((milliseconds / 1000) % 60)
  const minutes = Math.floor((milliseconds / (1000 * 60)) % 60)
  const hours = Math.floor((milliseconds / (1000 * 60 * 60)) % 24)

  const hoursStr = hours < 10 ? '0' + hours : hours
  const minutesStr = minutes < 10 ? '0' + minutes : minutes
  const secondsStr = seconds < 10 ? '0' + seconds : seconds

  if ((hoursStr + ':' + minutesStr + ':' + secondsStr === 'NaN:NaN:NaN')) return '<i>idle</i>'
  return hoursStr + ':' + minutesStr + ':' + secondsStr
}

function formatETA(milliseconds: number): string {
  const date = new Date(milliseconds)
  const timeString = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })


  if (isNaN(date.getTime()) || timeString === "07:00 PM") {
    return '<i>idle</i>'
  }

  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}


let expandedState: (string | undefined)[] = [];

const collapseAll = () => {
    expandedState = printers.value.filter(printer => printer.isInfoExpanded).map(printer => printer.id?.toString());
    printers.value.forEach(printer => printer.isInfoExpanded = false);
}

const restoreExpandedState = () => {
    printers.value.forEach(printer => {
        if (expandedState.includes(printer.id?.toString())) {
            printer.isInfoExpanded = true;
        }
    });
}

</script>

<template>
  <div class="container">
    <table ref="table">
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
      dragClass="hidden-ghost" v-if="printers.length > 0" @start="collapseAll" @end="restoreExpandedState">
        <template #item="{ element: printer }">
          <div v-if="printer.isInfoExpanded" class="expanded-info">
            <tr :id="printer.id">
              <PrinterRow :printer="printer" />
            </tr>
            <tr style="background-color: #cdcdcd;">
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Filament:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Layer:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Nozzle Temp:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span v-html="printer?.extruder_temp ? printer.extruder_temp + ' &deg;C' : ' <i>idle</i>'"></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Bed Temp:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span v-html="printer?.bed_temp ? printer.bed_temp + ' &deg;C' : ' <i>idle</i>'"></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Elapsed:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.elapsed_time!)"></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Remaining:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.remaining_time!)"></span>
                </div>
              </td>
              <td style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>Total:</b>
                </div>
                <div style="position: relative; top: 50%;">
                  <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatTime(printer.queue[0]?.job_client?.total_time!)"></span>
                </div>
              </td>
              <td class="border-extended" style="vertical-align: top; height: 100%;">
                <div style="position: relative; top: 0;">
                  <b>ETA:</b>
                </div>
                <div style="position: relative; top: 50%;;">
                  <span
                    v-html="printer?.status === 'colorchange' ? 'Waiting for filament change...' : formatETA(printer.queue[0]?.job_client?.eta!)"></span>
                </div>
              </td>
            </tr>
          </div>
          <tr v-else :id="printer.id">
            <PrinterRow :printer="printer" />
          </tr>
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
.border-extended {
  position: relative;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.hidden-ghost {
  opacity: 0;
}

.border-extended::after {
  content: "";
  position: absolute;
  right: 0px;
  top: -0.5px;
  bottom: 0;
  width: 1px;
  background: #929292;
  height: calc(100% + 1.5px);
}
th {
  user-select: none;
}

.expanded-info {
  display: contents;
}
</style>