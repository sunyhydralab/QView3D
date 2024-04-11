<script setup lang="ts">
import { computed, watch } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const pageNames: { [key: string]: string } = {
  '/': 'Home',
  '/queue': 'Queues',
  '/registration': 'Registration',
  '/submit': 'Submit Job',
  '/history': 'Job History',
  '/error': 'Error Log'
};

const currentPage = computed(() => pageNames[route.path]);
</script>

<template>
  <div style="position: sticky; top: 0;">
    <nav class="navbar navbar-expand-lg thick">
      <router-link to="/" class="navbar-brand">
        <img class="logo" src="../assets/QView3Dlogo.png" alt="QView3D Logo">
      </router-link>

      <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav"
        aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse justify-content-end" id="navbarNav" style="padding-right: 1rem;"> <!-- Add justify-content-end class here -->
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
            <router-link to="/submit" class="nav-link" active-class="active-tab">SUBMIT JOB</router-link>
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
  height: 30px;
  position: relative;
  right: 20px;
}

.navbar {
  /* background: #525060 !important; */
  background: #484848 !important;
}

.nav-link {
  font-size: 1.2em; /* Adjust the value as needed */
  font-weight: bold;
  padding-right: 1.5rem !important; /* Adjust the value as needed */
  color: #1b1b1b;
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
  color: #000000;
  font-weight: bold;
}

.nav-link:hover {
  color: #7561A9;
}

body {
  margin: 0;
  padding: 0;
}

.current-page {
  background-color: #7561A9;
  color: white;
  padding: 5px;
  display: inline-block;
  border-right: 2px solid #7561a9;
  border-bottom: 2px solid #7561a9;
  border-bottom-right-radius: 5px;
  position: relative;
  z-index: 1;
  box-shadow: 0 2px 6px -2px #303035;
  padding-left: 15px;
  padding-right: 15px;
}
</style>