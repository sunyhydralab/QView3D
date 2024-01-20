<script setup lang="ts">
</script>

<template>
  <section class="section">
    <!-- NAVBAR  -->
    <div>
      <nav class="navbar" role="navigation" aria-label="dropdown navigation">
        <div class="navbar-item has-dropdown is-active">
          <div class="navbar-dropdown">
            <!-- <a class="navbar-item"><LoginBadge/></a> -->
            <a class="navbar-item">
              <RouterLink to="/">Home</RouterLink>
            </a>
            <a class="navbar-item">
              <RouterLink to="/queue">Queues</RouterLink>
            </a>
            <a class="navbar-item">
              <RouterLink to="/registration">Registration</RouterLink>
            </a>
            <hr class="navbar-divider">
            <div class="navbar-item">
              <RouterLink to="/submit">Submit job</RouterLink>
            </div>
          </div>
        </div>
      </nav>
    </div>

    <nav class="navbar is-fixed-top" role="navigation" aria-label="main navigation">

      <div class="navbar-brand">

        <!-- Add the hamburger button -->
        <a role="button" class="navbar-burger" aria-label="menu"
          aria-expanded="false">
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
          <span aria-hidden="true"></span>
        </a>
      </div>

    </nav>
  </section>
</template>

<style scoped>
.icon {
  padding-right: 10px;
}

.button {
  margin: 15px;
}

.router-link {
  color: #00b1d2;
}

.router-link-active {
  font-weight: bold;
  border-top: 2px solid #00b1d2;
}

.navbar {
  border-bottom: 2px solid #00b1d2;
  /* You can change the color and thickness as needed */
}
</style>