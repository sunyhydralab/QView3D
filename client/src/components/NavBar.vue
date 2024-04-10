<script setup lang="ts">
</script>

<template>
  <nav class="navbar navbar-expand-lg thick" style="background-color: #60aeae;">
    <router-link to="/" class="navbar-brand" style="color: #7561a9;">QView3D</router-link>

    <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>

    <div class="collapse navbar-collapse" id="navbarNav">
      <ul class="navbar-nav mr-auto">
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

      <router-link to="/submit" class="btn btn-outline-success my-2 my-sm-0 ms-auto">Submit Job</router-link>
    </div>
  </nav>
</template>

<style scoped>
.btn{
  margin-right: 3%; 
}

.navbar-brand, .navbar-dropdown{
  margin-left: 2%; 
}

.thick {
  border-bottom: 2px solid #7561a9;
  box-shadow: 0 2px 6px -2px #7561a9;
  height: 65px;
}
.active-tab {
  color: #7561a9;
  font-weight: bold;
}

.nav-link:hover {
  color: #7561a9;
}
</style>