<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
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

            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>

            <div class="collapse navbar-collapse" id="navbarNav">
              <ul class="navbar-nav mr-auto" style="right: 20px; position: relative;">
                <li class="nav-item">
                  <router-link to="/" class="nav-link" active-class="active-tab">Home</router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/queue" class="nav-link" active-class="active-tab">Queues</router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/registration" class="nav-link" active-class="active-tab">Registration</router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/submit" class="nav-link" active-class="active-tab">Submit Job</router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/history" class="nav-link" active-class="active-tab">Job History</router-link>
                </li>
                <li class="nav-item">
                  <router-link to="/error" class="nav-link" active-class="active-tab">Error Log</router-link>
                </li>
              </ul>
            </div>
        </nav>
        <div class="current-page">
          {{ currentPage }}
        </div>
    </div>
</template>

<style scoped>
.logo{
  height: 30px;
  position: relative;
  right: 20px;
}

.btn{
  margin-right: 3%; 
}

.navbar-brand, .navbar-dropdown{
  margin-left: 2%; 
}

.thick {
  background-color: #fff;
  border-bottom: 2px solid #7561a9;
  box-shadow: 0 2px 6px -2px #7561a9;
}
.active-tab {
  color: #000;
}

.nav-link:hover {
  color: #7561a9;
}

body {
  margin: 0;
  padding: 0;
}

.current-page {
  background-color: #60aeae;
  color: white;
  padding: 5px;
  display: inline-block;
  border-right: 2px solid #7561a9;  
  border-bottom: 2px solid #7561a9;
  border-bottom-right-radius: 5px;
  position: relative;
  z-index: 1;
  color: #7561a9;
  font-weight: bold;
  box-shadow: 0 2px 6px -2px #7561a9;
}
</style>