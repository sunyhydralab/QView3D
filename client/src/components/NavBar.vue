<script setup lang="ts">
</script>

<template>
  <section class="section">
    <nav class="navbar navbar-expand-lg bg-body-tertiary d-flex justify-content-between">
      <RouterLink to='/' class="navbar-brand">Clever Name</RouterLink>
      <button class="btn btn-outline-success" type="submit">Submit Job</button>
    </nav>

    <div class="sidenav">
  <a href="#">About</a>
  <a href="#">Services</a>
  <a href="#">Clients</a>
  <a href="#">Contact</a>
</div>
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
.navbar{
  position: fixed;
  z-index: 2;
  padding-right: 5%;
  padding-left: 2%; 
}

.sidenav {
  height: 100%; /* Full-height: remove this if you want "auto" height */
  width: 160px; /* Set the width of the sidebar */
  position: fixed; /* Fixed Sidebar (stay in place on scroll) */
  z-index: 0; /* Stay on top */
  top: 70; /* Stay at the top */
  left: 0;
  background-color: #111; /* Black */
  overflow-x: hidden; /* Disable horizontal scroll */
  padding-top: 20px;
}

/* The navigation menu links */
.sidenav a {
  padding: 6px 8px 6px 16px;
  text-decoration: none;
  font-size: 25px;
  color: #818181;
  display: block;
}
.sidenav a:hover {
  color: #f1f1f1;
}

/* Style page content */
.main {
  margin-left: 160px; /* Same as the width of the sidebar */
  padding: 0px 10px;
  z-index: 1; /* Ensure content is on top of the sidebar */
}

/* On smaller screens, where height is less than 450px, change the style of the sidebar (less padding and a smaller font size) */
@media screen and (max-height: 450px) {
  .sidenav {padding-top: 15px;}
  .sidenav a {font-size: 18px;}
}
</style>