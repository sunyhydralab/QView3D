<script setup lang="ts">
</script>

<template>
  <section class="section">
    <nav class="navbar navbar-expand-lg bg-body-tertiary d-flex justify-content-between">
      <RouterLink to='/' class="navbar-brand">Clever Name</RouterLink>
      <button class="btn btn-outline-success" type="submit">Submit Job</button>
    </nav>

    <!-- NAVBAR  -->
    <div>
      <div class="navbar-dropdown">
        <a class="navbar-item">
          <RouterLink to="/">Home </RouterLink>
        </a>
        <a class="navbar-item">
          <RouterLink to="/queue">Queues </RouterLink>
        </a>
        <a class="navbar-item">
          <RouterLink to="/registration">Registration </RouterLink>
        </a>
        <a class="navbar-item">
          <RouterLink to="/submit">Submit job </RouterLink>
        </a>
      </div>
    </div>

  </section>
</template>

<style scoped>
/* .navbar{
  position: fixed;
  z-index: 2;
  padding-right: 5%;
  padding-left: 2%; 
} */

</style>