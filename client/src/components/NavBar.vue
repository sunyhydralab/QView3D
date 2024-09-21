<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { api } from '../model/myFetch';

const route = useRoute();

const isSubmitRoute = computed(() => route.path.startsWith('/submit'));

const clientVersion = import.meta.env.VITE_CLIENT_VERSION as string;
const serverVersion = ref<string | null>(null);

onMounted(async () => {
  serverVersion.value = await api('serverVersion');
});
</script>

<template>
  <div style="position: sticky; top: 0;">
    <nav class="navbar navbar-expand-lg thick">
      <div class="navbar-brand">
        <router-link to="/" class="navbar-brand">
          <img class="logo" src="../assets/QView3D.svg" alt="QView3D Logo">
        </router-link>
        <div class="client-version">v{{ clientVersion }} (v{{ serverVersion }}-serv)</div>
      </div>

      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse justify-content-end" id="navbarNav" style="padding-right: 1rem;">
        <!-- Add justify-content-end class here -->
        <ul class="navbar-nav">
          <li class="nav-item">
            <router-link to="/" class="nav-link" active-class="active-tab">HOME</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/queue" class="nav-link" active-class="active-tab">QUEUES</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/registration" class="nav-link" active-class="active-tab">REGISTRATION</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/submit" class="nav-link" :class="{ 'active-tab': isSubmitRoute }">SUBMIT JOB</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/history" class="nav-link" active-class="active-tab">JOB HISTORY</router-link>
          </li>
          <li class="nav-item">
            <router-link to="/error" class="nav-link" active-class="active-tab">ERROR LOG</router-link>
          </li>
        </ul>
      </div>
    </nav>
    <!-- <div class="current-page">
      {{ currentPage }}
    </div> -->
  </div>
</template>

<style scoped>
.logo {
  height: 100px;
  position: relative;
  right: 60px;
  margin-bottom: -2rem;
  margin-top: -1rem;
  ;
}

.navbar {
  /* background: #525060 !important; */
  background: #484848 !important;
}

.nav-link {
  font-size: 1.2em;
  /* Adjust the value as needed */
  font-weight: bold;
  padding-right: 1.5rem !important;
  /* Adjust the value as needed */
  color: #a8a8a8;
}

.form-check {
  padding-right: 20px;
}

.btn {
  margin-right: 3%;
}

.navbar-brand,
.navbar-dropdown {
  margin-left: 2%;
}

.thick {
  background-color: #fff;
  border-bottom: 2px solid #3b3b3b;
  box-shadow: 0 2px 6px -2px #000000;
}

.active-tab {
  color: #dbdbdb;
  font-weight: bolder;
}

body {
  margin: 0;
  padding: 0;
}

.client-version {
  font-size: 0.65em;
  color: #888888;
  margin-top: 0.5rem;
  text-align: center;
  position: relative;
  right: 60px; /* Aligns with the logo's position */
}
</style>