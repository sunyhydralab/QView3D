<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { printers, type Device } from '@/model/ports';
import GCode3DImageViewer from '@/components/GCode3DImageViewer.vue'
import GCodeThumbnail from '@/components/GCodeThumbnail.vue';
import { useAssignIssue, useGetIssues, type Issue } from '@/model/issues';
import { useAssignComment, useReleaseJob, type Job } from '@/model/jobs';
import NoPrinterRobot from '@/components/NoPrinterRobot.vue';
import ExpandedPrintView from '@/components/ExpandedPrintView.vue';

const { assign } = useAssignIssue()
const { assignComment } = useAssignComment()
const { releaseJob } = useReleaseJob()
const { issues } = useGetIssues()

const selectedIssue = ref<Issue>()
const selectedJob = ref<Job>()
const jobComments = ref('')

const currentJob = ref<Job>();

const issuelist = ref<Array<Issue>>([])

const isGcodeImageVisible = ref(false)
const isImageVisible = ref(true)

const isGcodeLiveViewVisible = ref(false)

onMounted(async () => {
  issuelist.value = await issues()

  const imageModal = document.getElementById('gcodeImageModal')

  imageModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeImageVisible.value = false;
    isImageVisible.value = true;
  });

  const liveModal = document.getElementById('gcodeLiveViewModal')

  liveModal?.addEventListener('hidden.bs.modal', () => {
    isGcodeLiveViewVisible.value = false;
  });
  if (printers.value.length > 0) {
    for (const printer of printers.value as Device[]) {
      if (printer.consoles === undefined) {
        printer.consoles = [[], [], [], [], []]
      }
    }
  }
});

const doAssignIssue = async () => {
  if (selectedJob.value === undefined) return
  await assignComment(selectedJob.value, jobComments.value)
  await releasePrinter(selectedJob.value, 3, selectedJob.value.printerid)

  if (selectedIssue.value !== undefined) {
    await assign(selectedIssue.value.id, selectedJob.value.id)
  }

  selectedJob.value.comments = jobComments.value
  selectedIssue.value = undefined
  selectedJob.value = undefined

  await nextTick()
}


const releasePrinter = async (jobToFind: Job | undefined, key: number, printerIdToPrintTo: number) => {

  let printer = printers.value.find((printer) => printer.id === printerIdToPrintTo)
  printer!.error = ""

  if (printer) {
    printer.extruder_temp = 0
    printer.bed_temp = 0;
    printer.queue?.shift(); // Remove the first job in the queue
    printer.consoles = [[], [], [], [], []]
    //TODO: marker
  }

  await releaseJob(jobToFind, key, printerIdToPrintTo)
  await nextTick()
}

</script>

<template>
  <div class="modal fade" id="issueModal" tabindex="-1" aria-labelledby="assignIssueLabel" aria-hidden="true"
    data-bs-backdrop="static">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header d-flex align-items-end">
          <h5 class="modal-title mb-0" id="assignIssueLabel" style="line-height: 1;">
            Job #{{ selectedJob?.td_id }}</h5>
          <h6 class="modal-title" id="assignIssueLabel" style="padding-left:10px; line-height: 1;">
            {{ selectedJob?.date }}</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"
            @click="selectedIssue = undefined; selectedJob = undefined;"></button>
        </div>
        <div class="modal-body">
          <form @submit.prevent="">
            <div class="mb-3">
              <label for="issue" class="form-label">Select Issue</label>
              <select name="issue" id="issue" v-model="selectedIssue" class="form-select" required>
                <option disabled value="undefined">Select Issue</option>
                <option v-for="issue in issuelist" :value="issue" :key="issue.id">
                  {{ issue.issue }}
                </option>
              </select>
            </div>
          </form>
          <div class="form-group mt-3">
            <label for="exampleFormControlTextarea1">Comments</label>
            <textarea class="form-control" id="exampleFormControlTextarea1" rows="3" v-model="jobComments"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal"
            @click="selectedIssue = undefined; selectedJob = undefined">Close</button>
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" @click="doAssignIssue">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeLiveViewModal' -->
  <div class="modal fade" id="gcodeLiveViewModal" tabindex="-1" aria-labelledby="gcodeLiveViewModalLaebl"
    aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered modal-xl">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeLiveViewModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}<br>
            <b>Z-Layer:</b> {{ currentJob?.current_layer_height }}/{{ currentJob?.max_layer_height }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DImageViewer v-if="isGcodeLiveViewVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- bootstrap 'gcodeImageModal' -->
  <div class="modal fade" id="gcodeImageModal" tabindex="-1" aria-labelledby="gcodeImageModalLabel" aria-hidden="true">
    <div :class="['modal-dialog', isImageVisible ? '' : 'modal-xl', 'modal-dialog-centered']">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="gcodeImageModalLabel">
            <b>{{ currentJob?.printer }}:</b> {{ currentJob?.name }}
            <div class="form-check form-switch">
              <label class="form-check-label" for="switchView">{{ isImageVisible ? 'Image' : 'Viewer'
                }}</label>
              <input class="form-check-input" type="checkbox" id="switchView" v-model="isImageVisible">
            </div>
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row">
            <GCode3DImageViewer v-if="isGcodeImageVisible && !isImageVisible" :job="currentJob" />
            <GCodeThumbnail v-else-if="isGcodeImageVisible && isImageVisible" :job="currentJob" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="container">
    <ExpandedPrintView />
    <NoPrinterRobot />
  </div>
</template>

<style scoped>
.btn-console {
  height: 2.5rem;
  width: 2.5rem;
  justify-content: center;
  border-radius: 20px;
}

.console, .viewer {
  padding: 0; 
  margin: 0; 
  border-spacing: 0;
}

.borderless-bottom {
  border-bottom: none !important;
  line-height: 11.5px;
}

.borderless-top {
  border-top: none !important;
  line-height: 10px;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.expanded-info {
  display: contents;
}

.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.buttons {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
}

.buttons>* {
  flex: 1 0 auto;
  margin: 0 0.375rem;
  flex-shrink: 0;
}


.dropdown-item {
  display: flex;
  align-items: center;
  padding-left: .5rem;
}

.dropdown-item i {
  width: 20px;
}

.dropdown-item span {
  margin-left: 10px;
}

.icon-disabled {
  color: #6e7073;
}

.not-draggable {
  pointer-events: none;
}

.sortable-chosen {
  opacity: 0.5;
  background-color: #f2f2f2;
}

.hidden-ghost {
  opacity: 0;
}

.buttons-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.buttons-progress>* {
  margin: 0 0.375rem;
}

.no-wrap {
  white-space: nowrap;
}

.form-control {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
}

.form-select {
  background-color: var(--color-background-soft);
  border-color: var(--color-border);
}

.alert {
  margin: 0;
  padding: 0.3rem;
}

.modern-table {
  border-collapse: separate;
  border-spacing: 0;
  border-radius: 8px;
  overflow: hidden;
}
</style>