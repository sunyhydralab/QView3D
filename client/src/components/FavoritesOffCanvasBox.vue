<script setup lang="ts">
import { useFavoriteJob, useGetJobFile, useGetJobs, type Job } from '@/model/jobs';
import { onMounted, ref } from 'vue'
import IsLoading from './IsLoading.vue';

const { getFavoriteJobs } = useGetJobs()

let jobs = ref<Array<Job>>([])
let favoriteJobs = ref<Array<Job>>([])
let buttonTransform = ref(0);
let isOffcanvasOpen = ref(false)
let jobToUnfavorite: Job | null = null;
const { getFileDownload } = useGetJobFile()
const { favorite } = useFavoriteJob()

onMounted(async () => {
    try {
        IsLoading.value = true;

        favoriteJobs.value = await getFavoriteJobs();
    } catch (error) {
        console.error(error);
    }
})

const toggleButton = () => {
  buttonTransform.value = buttonTransform.value === 0 ? -700 : 0
  isOffcanvasOpen.value = !isOffcanvasOpen.value
}

const favoriteJob = async (job: Job, fav: boolean) => {
    await favorite(job, fav);
    favoriteJobs.value = await getFavoriteJobs();

    jobs.value = jobs.value.map(j => {
        if (j.id === job.id) {
            j.favorite = fav;
        }
        return j;
    })

    jobToUnfavorite = null;
}

</script>

<template>
  <!-- bootstrap off canvas to the right -->
  <div
    class="offcanvas offcanvas-end"
    data-bs-backdrop="static"
    tabindex="-1"
    id="offcanvasRight"
    aria-labelledby="offcanvasRightLabel"
  >
    <div class="offcanvas-header">
      <div class="container-fluid">
        <div class="row align-items-center">
          <div class="col">
            <h5 class="offcanvas-title " id="offcanvasRightLabel">Favorite Prints</h5>
          </div>
          <div class="col-auto">
            <button
              type="button"
              class="btn-close btn-close-white"
              data-bs-dismiss="offcanvas"
              aria-label="Close"
              v-on:click="toggleButton"
            ></button>
          </div>
        </div>
      </div>
    </div>
    <div class="offcanvas-body" style="max-height: 100vh; overflow-y: auto">
      <div class="grid-container header">
        <h5>Job Name</h5>
        <h5>File Name</h5>
        <h5>Actions</h5>
      </div>
      <div v-if="favoriteJobs.length > 0">
        <div v-for="job in favoriteJobs" :key="job.id" class="mb-3">
          <div class="grid-container job">
            <p class="my-auto truncate-name">{{ job.name }}</p>
            <p class="my-auto truncate-file">{{ job.file_name_original }}</p>
            <div class="d-flex align-items-center">
              <i
                class="fas fa-star"
                style="margin-right: 10px"
                data-bs-toggle="modal"
                data-bs-target="#favoriteModal"
                @click="jobToUnfavorite = job"
              ></i>
              <button
                class="btn btn-secondary download"
                style="margin-right: 10px"
                @click="getFileDownload(job.id)"
                :disabled="job.file_name_original.includes('.gcode:')"
              >
                <i class="fas fa-download"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="text-center" style="color: var(--color-nav-text)">
        No favorite jobs found. Favorite your first job!
      </p>
    </div>
  </div>
  <div class="offcanvas-btn-box" :style="{ transform: `translateX(${buttonTransform}px)` }">
    <button
      class="btn btn-primary"
      type="button"
      data-bs-toggle="offcanvas"
      data-bs-target="#offcanvasRight"
      aria-controls="offcanvasRight"
      v-on:click="toggleButton"
      style="border-top-right-radius: 0; border-bottom-right-radius: 0; padding: 5px 10px"
    >
      <span v-if="isOffcanvasOpen"><i class="fas fa-star"></i></span>
      <span
        ><i class="fas" :class="isOffcanvasOpen ? 'fa-chevron-right' : 'fa-chevron-left'"></i
      ></span>
      <span v-if="!isOffcanvasOpen"><i class="fas fa-star"></i></span>
    </button>
  </div>

  <!-- modal to unfavorite a job in the off canvas -->
  <div class="modal fade" id="favoriteModal" tabindex="-1" aria-labelledby="favoriteModalLabel" aria-hidden="true"
        data-bs-backdrop="static">
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="favoriteModalLabel">Unfavorite Job</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p>Are you sure you want to unfavorite this job?</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    <button type="button" class="btn btn-primary" data-bs-dismiss="modal"
                        @click="favoriteJob(jobToUnfavorite!, false)">Unfavorite</button>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.border-top {
    margin: 5px;;
}

.sticky {
    position: sticky;
    bottom: 0px;
    background: var(--color-modal-background);
    margin-right: -1rem;
    margin-left: -1rem;
}

.truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.dropdown-card {
    position: absolute !important;
    top: calc(100% + 2px) !important;
    /* Adjust this value to increase or decrease the gap */
    width: 400px;
    z-index: 1000;
    background: var(--color-background-mute);
    border: 1px solid var(--color-border);
    padding-bottom: 0 !important;
}

.dropdown-submenu {
    position: relative;
    box-sizing: border-box;
}

.dropdown-submenu .dropdown-menu {
    top: -9px;
    right: 100%;
    max-height: 200px;
    overflow-y: auto;
}

.dropdown-submenu:hover>.dropdown-menu {
    display: block;
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

.truncate-name {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.truncate-file {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.grid-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    gap: 10px;
}

.job {
    padding: 10px;
    border-radius: 5px;
    background-color: var(--color-background-mute);
}

.offcanvas {
    width: 700px;
}

.offcanvas-btn-box {
    transition: transform .3s ease-in-out;
    position: fixed;
    top: 50%;
    right: 0;
    z-index: 1041;
}

.offcanvas-end {
    border-left: 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

ul.dropdown-menu.w-100.show li {
    margin-left: 1rem;
}

ul.dropdown-menu.w-100.show li.divider {
    margin-left: 0;
}

/*.form-check-input:focus,
.form-control:focus {
    outline: none;
    box-shadow: none;
    border-color: #e2e2e2;
}*/

label.form-check-label {
    cursor: pointer;
}

.form-control {
    background: var(--color-background);
    color: var(--color-background-font);
    border: 1px solid var(--color-border);
}

.form-select {
    background-color: var(--color-background);
    color: var(--color-background-font);
    border-color: var(--color-border);
}
</style>
